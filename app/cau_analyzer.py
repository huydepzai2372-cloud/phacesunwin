from typing import Dict, Optional


def get_cau_signal(profile: Dict) -> Optional[Dict]:
    """
    Analyze recent game history to get a 'cầu' (betting trend) signal.
    Returns a signal dict with value, label, and detail, or None if insufficient data.
    
    Args:
        profile: The player's profile dict
        
    Returns:
        Dict with 'value', 'label', and 'detail' keys, or None if no signal
    """
    history = [entry["result"] for entry in profile.get("history", [])[-8:]]
    if len(history) < 4:
        return None

    t_count = history.count("t")
    x_count = history.count("x")
    last = history[-1]
    previous = history[-2]

    # Three consecutive same results
    if last == previous == history[-3]:
        return {"value": last, "label": "TÀI" if last == "t" else "XỈU", "detail": "Cầu bền 3 ván liền"}

    # Strong dominance in recent 8 rounds
    if t_count >= x_count + 2:
        return {"value": "t", "label": "TÀI", "detail": "Tài chiếm ưu thế trong 8 ván gần nhất"}
    if x_count >= t_count + 2:
        return {"value": "x", "label": "XỈU", "detail": "Xỉu chiếm ưu thế trong 8 ván gần nhất"}

    # Last two results are same
    if last == previous:
        return {"value": last, "label": "TÀI" if last == "t" else "XỈU", "detail": "Cầu lặp gần nhất"}

    # Balanced distribution, no clear signal
    if abs(t_count - x_count) <= 1:
        return None

    # Slight dominance
    return {"value": "t", "label": "TÀI", "detail": "Xu hướng đang nghiêng Tài"} if t_count > x_count else {"value": "x", "label": "XỈU", "detail": "Xu hướng đang nghiêng Xỉu"}
