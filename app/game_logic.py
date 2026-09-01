import random
from typing import Dict, Optional

from app.config import INTEREST_RATE, WIN_THRESHOLD, GAME_MODE, BUFF_POOL, EVENT_POOL


def apply_interest(profile: Dict) -> None:
    """Apply interest to debt if player has outstanding debt."""
    if profile["debt"] > 0:
        profile["debt"] = int(profile["debt"] * (1 + INTEREST_RATE))


def record_round(profile: Dict, round_info: Dict) -> None:
    """Record a round result in the profile history and update stats."""
    profile["history"].append(round_info)
    stats = profile["stats"]
    stats["rounds"] += 1
    if round_info["payout"] > 0:
        stats["wins"] += 1
        stats["biggest_win"] = max(stats["biggest_win"], round_info["payout"])
    else:
        stats["losses"] += 1
        stats["biggest_loss"] = max(stats["biggest_loss"], abs(round_info["payout"]))
    stats["peak_balance"] = max(stats["peak_balance"], profile["balance"])
    stats["max_debt"] = max(stats["max_debt"], profile["debt"])


def roll_dice() -> tuple:
    """Roll three dice and return their values."""
    return random.randint(1, 6), random.randint(1, 6), random.randint(1, 6)


def determine_result(total: int) -> str:
    """Determine if result is 'tài' (t) or 'xỉu' (x) based on dice total."""
    return "t" if total >= WIN_THRESHOLD else "x"


def calculate_payout(
    choice: str,
    result: str,
    bet: int,
    multiplier: float,
    cau_hint: Optional[str],
    buff: Optional[Dict],
    event: Optional[Dict],
    force_loss: bool = False,
) -> tuple:
    """
    Calculate payout for a round and return (payout_amount, bonus_message).
    """
    bonus_message = ""
    
    if choice == result and not force_loss:
        # Win
        payout_amount = int(bet * multiplier)
        if cau_hint == choice:
            payout_amount += int(payout_amount * 0.1)
            bonus_message += " + cầu đúng"
        if buff and buff["kind"] in {"win_bonus", "win_extra"}:
            payout_amount += int(payout_amount * buff["value"])
            bonus_message += f" + bùa {buff['name']}"
        if event and event["kind"] == "cash_bonus":
            payout_amount += event["value"]
            bonus_message += " + sự kiện Mưa tiền"
        return payout_amount, bonus_message
    else:
        # Loss
        loss_amount = bet
        if cau_hint == choice:
            loss_amount = max(1, int(loss_amount * 0.9))
            bonus_message += " + cầu đúng"
        if buff and buff["kind"] == "safe_loss":
            loss_amount = max(1, int(bet * buff["value"]))
            bonus_message += f" + bùa {buff['name']}"
        if event and event["kind"] == "loss_cut":
            loss_amount = max(1, int(loss_amount * (1 - event["value"])))
            bonus_message += " + sự kiện Bão giang hồ"
        return -loss_amount, bonus_message
