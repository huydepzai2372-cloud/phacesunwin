import os
import secrets
from pathlib import Path
from urllib.parse import quote, urlencode

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.cau_analyzer import get_cau_signal
from app.config import BUFF_POOL, EVENT_POOL, GAME_MODE
from app.database import create_user, get_user_by_email, init_db, verify_user
from app.game_logic import (
    apply_interest,
    calculate_payout,
    determine_result,
    record_round,
    roll_dice,
)
from app.profile_manager import create_profile, load_saved_profiles, save_profiles

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret")

app = FastAPI(title="Sòng Bạc Web", version="1.0.0")
init_db()

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class CreateProfileRequest(BaseModel):
    name: str


class PlayRequest(BaseModel):
    profile_name: str
    choice: str
    bet: int = 0
    bet_type: str = "custom"


def get_user_from_header(request: Request):
    email = request.headers.get("x-user-email", "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="Bạn cần đăng nhập trước")
    user = get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=401, detail="Tài khoản không hợp lệ")
    return user


@app.get("/")
async def index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Sòng Bạc API is running"}


@app.get("/health")
async def health():
    return {"status": "ok", "app": "song-bac-web"}


@app.get("/auth/google/login")
async def google_login():
    if not GOOGLE_CLIENT_ID:
        return RedirectResponse(url="/?auth_error=google_not_configured", status_code=302)

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    target = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    response = RedirectResponse(url=target)
    response.set_cookie(
        key="google_oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        secure=False,
    )
    return response


@app.get("/auth/google/callback")
async def google_callback(request: Request):
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return RedirectResponse(url="/?auth_error=google_not_configured", status_code=302)

    code = request.query_params.get("code")
    state = request.query_params.get("state")
    cookie_state = request.cookies.get("google_oauth_state")

    if not code or not state or state != cookie_state:
        raise HTTPException(status_code=400, detail="Yêu cầu Google OAuth không hợp lệ")

    token_payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        token_response = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
        token_response.raise_for_status()
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Không lấy được access token từ Google")

        user_info_response = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_info_response.raise_for_status()
        profile = user_info_response.json()

    email = (profile.get("email") or "").strip().lower()
    name = (profile.get("name") or profile.get("given_name") or email.split("@", 1)[0]).strip()
    if not email:
        raise HTTPException(status_code=400, detail="Google không trả về email hợp lệ")

    user = get_user_by_email(email)
    if user is None:
        user = create_user(email=email, name=name, password=f"google_{secrets.token_urlsafe(16)}")

    redirect = RedirectResponse(url=f"/?google_auth=1&email={quote(email)}&name={quote(name)}")
    redirect.delete_cookie("google_oauth_state")
    return redirect


@app.post("/api/auth/signup")
async def signup(request: SignupRequest):
    email = request.email.strip().lower()
    name = request.name.strip()
    password = request.password.strip()

    if not name or not email or not password:
        raise HTTPException(status_code=400, detail="Tên, email và mật khẩu không được để trống")
    if get_user_by_email(email):
        raise HTTPException(status_code=400, detail="Email đã tồn tại")

    user = create_user(email=email, name=name, password=password)
    return {"message": "Đăng ký thành công", "user": user}


@app.post("/api/auth/login")
async def login(request: LoginRequest):
    user = verify_user(request.email.strip().lower(), request.password.strip())
    if user is None:
        raise HTTPException(status_code=401, detail="Email hoặc mật khẩu không đúng")
    return {"message": "Đăng nhập thành công", "user": user}


@app.get("/api/profiles")
async def get_profiles(request: Request):
    user = get_user_from_header(request)
    profiles = load_saved_profiles(user["email"])
    return {"profiles": profiles}


@app.get("/api/leaderboard")
async def get_leaderboard(request: Request):
    user = get_user_from_header(request)
    profiles = load_saved_profiles(user["email"])
    rows = []
    for name, profile in profiles.items():
        stats = profile.get("stats", {})
        rounds = stats.get("rounds", 0)
        winrate = (stats.get("wins", 0) / rounds * 100) if rounds else 0.0
        rows.append(
            {
                "name": name,
                "balance": profile.get("balance", 0),
                "debt": profile.get("debt", 0),
                "rounds": rounds,
                "wins": stats.get("wins", 0),
                "losses": stats.get("losses", 0),
                "biggest_win": stats.get("biggest_win", 0),
                "winrate": round(winrate, 2),
            }
        )
    rows.sort(key=lambda item: (item["balance"], item["biggest_win"]), reverse=True)
    return {"leaderboard": rows[:10]}


@app.get("/api/history")
async def get_history(request: Request, profile_name: str | None = None):
    user = get_user_from_header(request)
    profiles = load_saved_profiles(user["email"])
    if profile_name:
        profile = profiles.get(profile_name)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return {"profile": profile_name, "history": profile.get("history", [])}

    summary = []
    for name, profile in profiles.items():
        stats = profile.get("stats", {})
        summary.append(
            {
                "name": name,
                "rounds": stats.get("rounds", 0),
                "wins": stats.get("wins", 0),
                "losses": stats.get("losses", 0),
                "balance": profile.get("balance", 0),
                "debt": profile.get("debt", 0),
            }
        )
    summary.sort(key=lambda item: item["rounds"], reverse=True)
    return {"history": summary}


@app.post("/api/profiles")
async def create_profile_api(request: Request, payload: CreateProfileRequest):
    user = get_user_from_header(request)
    profiles = load_saved_profiles(user["email"])
    name = payload.name.strip() or "Người chơi"

    if name in profiles:
        return {"message": "Profile already exists", "profile": profiles[name]}

    profile = create_profile(name, user_email=user["email"])
    profiles[name] = profile
    save_profiles(profiles, user["email"])
    return {"message": "Profile created", "profile": profile}


@app.post("/api/play")
async def play_round(request: Request, payload: PlayRequest):
    user = get_user_from_header(request)
    profiles = load_saved_profiles(user["email"])
    profile = profiles.get(payload.profile_name)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    choice = payload.choice.lower()
    if choice not in {"t", "x"}:
        raise HTTPException(status_code=400, detail="Choice must be 't' or 'x'")

    if profile["balance"] <= 0 and profile["debt"] <= 0:
        raise HTTPException(status_code=400, detail="Bạn hết tiền và không thể tiếp tục")

    if payload.bet_type == "all":
        bet = profile["balance"]
        multiplier = GAME_MODE["multiplier_all"]
    elif payload.bet_type == "half":
        bet = max(1, profile["balance"] // 2)
        multiplier = GAME_MODE["multiplier_half"]
    else:
        bet = int(payload.bet)
        multiplier = GAME_MODE["multiplier_half"]

    if bet <= 0:
        raise HTTPException(status_code=400, detail="Cược phải lớn hơn 0")
    if bet > profile["balance"]:
        raise HTTPException(status_code=400, detail="Bạn không đủ tiền để cược")

    if not profile.get("buff") and len(profile["history"]) % 3 == 0:
        profile["buff"] = BUFF_POOL[0]
    if not profile.get("event") and len(profile["history"]) % 5 == 0:
        profile["event"] = EVENT_POOL[0]

    signal = get_cau_signal(profile)
    cau_hint = signal["value"] if signal else None

    if profile["debt"] > 0:
        apply_interest(profile)

    x1, x2, x3 = roll_dice()
    total = x1 + x2 + x3
    result = determine_result(total)

    force_loss = profile["balance"] > 750 and __import__("random").random() < 0.5
    payout, bonus_message = calculate_payout(
        choice,
        result,
        bet,
        multiplier,
        cau_hint,
        profile.get("buff"),
        profile.get("event"),
        force_loss,
    )

    profile["balance"] += payout
    if profile["balance"] < 0:
        profile["balance"] = 0

    event = profile.get("event")
    if event and event["kind"] == "lucky_pick" and choice == result:
        profile["balance"] += event["value"]

    round_info = {
        "round": len(profile["history"]) + 1,
        "bet": bet,
        "choice": choice,
        "dice": f"{x1},{x2},{x3}",
        "total": total,
        "result": result,
        "payout": payout,
        "balance": profile["balance"],
        "debt": profile["debt"],
    }

    profile["recent_results"].append("TÀI" if result == "t" else "XỈU")
    profile["recent_results"] = profile["recent_results"][-5:]
    record_round(profile, round_info)

    for quest in profile.get("quests", []):
        if quest["completed"]:
            continue
        if quest["type"] == "win" and round_info["payout"] > 0:
            quest["progress"] += 1
        elif quest["type"] == "rounds":
            quest["progress"] += 1
        elif quest["type"] == "balance" and profile["balance"] >= quest["target"]:
            quest["progress"] = quest["target"]
        if quest["progress"] >= quest["target"]:
            quest["completed"] = True
            profile["balance"] += quest["reward"]

    profile["buff"] = None
    profile["event"] = None
    save_profiles(profiles, user["email"])

    return {
        "message": "Round resolved",
        "result": result,
        "choice": choice,
        "dice": [x1, x2, x3],
        "total": total,
        "bet": bet,
        "payout": payout,
        "bonus_message": bonus_message,
        "balance": profile["balance"],
        "debt": profile["debt"],
        "profile": profile,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
