from tools import verify


def test_same_colour_tolerates_rounding_jitter():
    assert verify.same_colour("rgb(113, 142, 113)", "rgb(112, 143, 111)")
    assert not verify.same_colour("rgb(255, 255, 255)", "rgb(112, 143, 111)")
    assert not verify.same_colour("rgb(116, 143, 111)", "rgb(112, 143, 111)")


def test_dim_tab_colour_is_never_white():
    assert verify.dim_problem("rgb(255, 255, 255)")
    assert verify.dim_problem("rgb(254, 253, 255)")
    assert verify.dim_problem("rgb(135, 144, 189)") is None
