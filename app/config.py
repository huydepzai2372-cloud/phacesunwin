import os
from typing import Dict

# Game configuration constants
INITIAL_BALANCE = 100
INTEREST_RATE = 0.2  # Lãi suất nợ mỗi ván
HOUSE_FEE_RATE = 0.2  # Phí giang hồ khi thắng còn nợ
WIN_THRESHOLD = 11  # Tổng xúc xắc >= 11 là tài, else xỉu
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
os.makedirs(DATA_DIR, exist_ok=True)
SAVE_FILE = os.path.join(DATA_DIR, "songo_save.json")
DATABASE_PATH = os.path.join(DATA_DIR, "profiles.db")

# Default game mode is now hardcoded to "normal"
DEFAULT_MODE = "normal"

GAME_MODE = {
    "label": "Bình thường",
    "description": "Cược tự do, all-in 2x, nửa 1.5x.",
    "multiplier_all": 2.0,
    "multiplier_half": 1.5,
    "max_bet_ratio": 1.0,
    "allow_half": True,
    "allow_debt": True,
}

BUFF_POOL = [
    {"name": "Mắt quỷ", "kind": "win_bonus", "value": 0.5, "desc": "+50% tiền thắng"},
    {"name": "Tấm khiên", "kind": "safe_loss", "value": 0.7, "desc": "Thua chỉ mất 70%"},
    {"name": "Lửa giang hồ", "kind": "win_extra", "value": 0.35, "desc": "+35% thưởng khi thắng"},
]

EVENT_POOL = [
    {"name": "Mưa tiền", "kind": "cash_bonus", "value": 25, "desc": "+25K nếu thắng"},
    {"name": "Đêm lạ", "kind": "lucky_pick", "value": 15, "desc": "+15K nếu chọn đúng"},
    {"name": "Bão giang hồ", "kind": "loss_cut", "value": 0.2, "desc": "Giảm 20% thiệt hại khi thua"},
]

QUEST_TEMPLATE = [
    {"id": "win3", "title": "Thắng 3 ván", "type": "win", "target": 3, "reward": 30, "progress": 0, "completed": False},
    {"id": "round10", "title": "Chơi 10 ván", "type": "rounds", "target": 10, "reward": 40, "progress": 0, "completed": False},
    {"id": "balance150", "title": "Vượt 150K", "type": "balance", "target": 150, "reward": 60, "progress": 0, "completed": False},
]
