import json
from typing import Dict

from app.config import SAVE_FILE, INITIAL_BALANCE, QUEST_TEMPLATE
from app.database import load_profiles, save_profiles as save_profiles_db


def load_saved_profiles(user_email: str | None = None) -> Dict[str, Dict]:
    """Load all saved profiles from the database if available, otherwise fallback to JSON."""
    try:
        profiles = load_profiles(user_email)
        if profiles:
            return profiles
    except Exception:
        pass

    import os
    if not os.path.exists(SAVE_FILE):
        return {}
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if user_email is None:
                return data
            return {name: profile for name, profile in data.items() if profile.get("user_email") == user_email}
    except (json.JSONDecodeError, OSError):
        return {}


def save_profiles(profiles: Dict[str, Dict], user_email: str | None = None) -> None:
    """Save all profiles to database and keep JSON fallback for compatibility."""
    try:
        save_profiles_db(profiles, user_email)
    except Exception:
        pass

    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


def create_profile(name: str, user_email: str | None = None) -> Dict:
    """Create a new player profile with default settings."""
    profile = {
        "name": name,
        "user_email": user_email,
        "mode": "normal",
        "balance": INITIAL_BALANCE,
        "debt": 0,
        "history": [],
        "buff": None,
        "event": None,
        "recent_results": [],
        "quests": [dict(item) for item in QUEST_TEMPLATE],
        "stats": {
            "rounds": 0,
            "wins": 0,
            "losses": 0,
            "biggest_win": 0,
            "biggest_loss": 0,
            "peak_balance": INITIAL_BALANCE,
            "max_debt": 0,
        },
    }
    return profile


def get_leaderboard_data(profiles: Dict[str, Dict]) -> str:
    """Generate leaderboard text from profiles."""
    from app.utils import format_money
    
    if not profiles:
        return "Chưa có hồ sơ nào được lưu."
    
    lines = ["TOP người chơi theo số dư, thắng lớn và tỷ lệ thắng:\n"]
    
    # Top by balance
    sorted_balance = sorted(profiles.items(), key=lambda x: x[1]["balance"], reverse=True)[:10]
    lines.append("--- TOP số dư ---\n")
    for rank, (name, profile) in enumerate(sorted_balance, start=1):
        lines.append(
            f"{rank}. {name:15} | Dư: {format_money(profile['balance']):10} | Nợ: {format_money(profile['debt'])}\n"
        )
    
    # Top by win rate
    winrate_profiles = [p for p in profiles.items() if p[1]["stats"]["rounds"] > 0]
    sorted_winrate = sorted(winrate_profiles, key=lambda x: x[1]["stats"]["wins"] / x[1]["stats"]["rounds"], reverse=True)[:10]
    lines.append("\n--- TOP tỷ lệ thắng ---\n")
    for rank, (name, profile) in enumerate(sorted_winrate, start=1):
        rounds = profile["stats"]["rounds"]
        win_rate = profile["stats"]["wins"] / rounds * 100
        lines.append(
            f"{rank}. {name:15} | Winrate: {win_rate:5.1f}% ({profile['stats']['wins']}/{rounds})\n"
        )
    
    # Top by biggest win
    lines.append("\n--- TOP thắng lớn ---\n")
    sorted_max = sorted(profiles.items(), key=lambda x: x[1]["stats"]["biggest_win"], reverse=True)[:10]
    for rank, (name, profile) in enumerate(sorted_max, start=1):
        lines.append(
            f"{rank}. {name:15} | Biggest win: {format_money(profile['stats']['biggest_win'])}\n"
        )
    
    return "".join(lines)
