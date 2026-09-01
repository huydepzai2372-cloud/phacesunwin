from app.game_logic import calculate_payout, determine_result, roll_dice


def test_determine_result():
    assert determine_result(11) == "t"
    assert determine_result(10) == "x"


def test_calculate_payout_win():
    payout, message = calculate_payout("t", "t", 20, 2.0, None, None, None, False)
    assert payout == 40
    assert message == ""


def test_calculate_payout_loss():
    payout, message = calculate_payout("t", "x", 20, 2.0, None, None, None, False)
    assert payout == -20
    assert message == ""


def test_roll_dice_range():
    a, b, c = roll_dice()
    assert 1 <= a <= 6
    assert 1 <= b <= 6
    assert 1 <= c <= 6
