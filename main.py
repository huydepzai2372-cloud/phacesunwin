from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.cau_analyzer import get_cau_signal
from app.config import BUFF_POOL, EVENT_POOL, GAME_MODE
from app.database import init_db
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

app = FastAPI(title="Sòng Bạc Web", version="1.0.0")
init_db()

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class CreateProfileRequest(BaseModel):
    name: str


class PlayRequest(BaseModel):
    profile_name: str
    choice: str
    bet: int = 0
    bet_type: str = "custom"


@app.get("/")
async def index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Sòng Bạc API is running"}


@app.get("/health")
async def health():
    return {"status": "ok", "app": "song-bac-web"}


@app.get("/api/profiles")
async def get_profiles():
    profiles = load_saved_profiles()
    return {"profiles": profiles}


@app.get("/api/profiles/{profile_name}")
async def get_profile(profile_name: str):
    profiles = load_saved_profiles()
    profile = profiles.get(profile_name)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return {"profile": profile}


@app.get("/api/leaderboard")
async def get_leaderboard():
    profiles = load_saved_profiles()
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
async def get_history(profile_name: str | None = None):
    profiles = load_saved_profiles()
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
async def create_profile_api(request: CreateProfileRequest):
    profiles = load_saved_profiles()
    name = request.name.strip() or "Người chơi"

    if name in profiles:
        return {"message": "Profile already exists", "profile": profiles[name]}

    profile = create_profile(name)
    profiles[name] = profile
    save_profiles(profiles)
    return {"message": "Profile created", "profile": profile}


@app.post("/api/play")
async def play_round(request: PlayRequest):
    profiles = load_saved_profiles()
    profile = profiles.get(request.profile_name)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    choice = request.choice.lower()
    if choice not in {"t", "x"}:
        raise HTTPException(status_code=400, detail="Choice must be 't' or 'x'")

    if profile["balance"] <= 0 and profile["debt"] <= 0:
        raise HTTPException(status_code=400, detail="Bạn hết tiền và không thể tiếp tục")

    if request.bet_type == "all":
        bet = profile["balance"]
        multiplier = GAME_MODE["multiplier_all"]
    elif request.bet_type == "half":
        bet = max(1, profile["balance"] // 2)
        multiplier = GAME_MODE["multiplier_half"]
    else:
        bet = int(request.bet)
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
    save_profiles(profiles)

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
