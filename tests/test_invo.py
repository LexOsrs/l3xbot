from cogs.invo import pick_best_invocations, SOFTCORE_RUN, SHAKING_THINGS_UP

def test_pick_15():
    result = pick_best_invocations(15)
    assert result == [SOFTCORE_RUN], f"Expected [SOFTCORE_RUN], got {result}"

def test_pick_10():
    result = pick_best_invocations(10)
    assert result == [SHAKING_THINGS_UP], f"Expected [SHAKING_THINGS_UP], got {result}"
