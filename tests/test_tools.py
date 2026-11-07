"""Tests for the five analytical tools and the MCP server.  Run:  python -m pytest -q"""
import asyncio
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tools  # noqa: E402
from server import mcp  # noqa: E402
from mcp import Client  # noqa: E402


# ---------------------------------------------------------------- HW4 tools (same tests as HW4)

def test_hw4_tools_unchanged():
    r1 = tools.check_functional_geometry(20, 2, 50, 2, 45)
    r2 = tools.check_recovery_feasibility(2, 0.25, 15, 0.2)
    r3 = tools.expected_recovery_savings(5, 2, 0.25, 120, 50, 0.8)
    assert math.isclose(r1["estimated_capacity_mL"], math.pi * 18**2 * 48 / 1000, abs_tol=1e-3)
    assert r1["meets_requirement"]
    assert r2["required_layers"] == 8 and math.isclose(r2["transition_height_mm"], 1.6) and r2["feasible"]
    assert math.isclose(r3["expected_time_savings_h"], 1.75) and math.isclose(r3["expected_filament_savings_g"], 46)
    assert tools.check_recovery_feasibility(0, 0.25, 0, 0.2)["required_layers"] == 0
    assert tools.check_recovery_feasibility(2, 0.25, 7, 0.2)["feasible"] is False


@pytest.mark.parametrize("fn, args", [
    (tools.check_functional_geometry, (20, 25, 50, 2, 45)),         # wall thicker than radius
    (tools.check_recovery_feasibility, (2, 0, 15, 0.2)),            # zero per-layer limit
    (tools.expected_recovery_savings, (5, 2, 0.25, 120, 50, 80)),   # 80 instead of 0.8
])
def test_hw4_invalid_inputs(fn, args):
    with pytest.raises(ValueError):
        fn(*args)


# ---------------------------------------------------------------- Tool 4: early-stop trend alarm

DEMO_TREND = dict(layer_numbers=[10, 20, 30, 40, 50], deviations_mm=[0.05, 0.10, 0.16, 0.21, 0.25],
                  tolerance_mm=0.5, total_layers=200, total_print_time_h=8, total_filament_g=150)


def test_trend_stop_hand_check():
    r = tools.early_stop_trend_alarm(**DEMO_TREND)
    # Hand least squares: mean n = 30, mean d = 0.154, Sxx = 1000, Sxy = 5.1 -> b = 0.0051, a = 0.001
    assert math.isclose(r["trend_slope_mm_per_layer"], 0.0051, abs_tol=1e-6)
    # Projection to layer 200: 0.001 + 0.0051*200 = 1.021 mm > 0.5 mm tolerance -> STOP
    assert math.isclose(r["projected_final_deviation_mm"], 1.021, abs_tol=1e-4)
    assert r["alert_level"] == "STOP"
    # Exceedance: (0.5 - 0.001)/0.0051 = 97.84 -> layer 98, i.e. 48 layers from now
    assert r["projected_exceedance_layer"] == 98 and r["layers_until_exceedance"] == 48
    # Stopping at layer 50 of 200 saves 75% of 8 h and 150 g
    assert math.isclose(r["time_saved_if_stopped_now_h"], 6.0)
    assert math.isclose(r["filament_saved_if_stopped_now_g"], 112.5)


def test_trend_ok_and_watch():
    flat = tools.early_stop_trend_alarm([10, 20, 30], [0.05, 0.05, 0.05], 0.5, 200)
    assert flat["alert_level"] == "OK" and flat["projected_exceedance_layer"] is None
    assert flat["time_saved_if_stopped_now_h"] is None
    # 0.3 mm now (>= 0.25 = 50% of tolerance) but flat trend -> WATCH, not STOP
    watch = tools.early_stop_trend_alarm([10, 20, 30], [0.3, 0.3, 0.3], 0.5, 200)
    assert watch["alert_level"] == "WATCH"
    # Already over tolerance -> STOP at the current layer
    over = tools.early_stop_trend_alarm([10, 20, 30], [0.2, 0.4, 0.6], 0.5, 200)
    assert over["alert_level"] == "STOP" and over["layers_until_exceedance"] == 0


@pytest.mark.parametrize("kwargs", [
    dict(layer_numbers=[10, 20], deviations_mm=[0.1, 0.2], tolerance_mm=0.5, total_layers=100),       # too few points
    dict(layer_numbers=[10, 20, 30], deviations_mm=[0.1, 0.2], tolerance_mm=0.5, total_layers=100),   # length mismatch
    dict(layer_numbers=[10, 30, 20], deviations_mm=[0.1, 0.2, 0.3], tolerance_mm=0.5, total_layers=100),  # not increasing
    dict(layer_numbers=[10, 20, 300], deviations_mm=[0.1, 0.2, 0.3], tolerance_mm=0.5, total_layers=100),  # past end
    dict(layer_numbers=[10, 20, 30], deviations_mm=[0.1, -0.2, 0.3], tolerance_mm=0.5, total_layers=100),  # negative
])
def test_trend_invalid_inputs(kwargs):
    with pytest.raises(ValueError):
        tools.early_stop_trend_alarm(**kwargs)


# ---------------------------------------------------------------- Tool 5: layer-shift strength check

DEMO_SHIFT = dict(section_width_mm=20, section_depth_mm=10, shift_mm=4, axial_force_N=500,
                  bending_moment_Nmm=0, tensile_strength_MPa=50, interlayer_strength_factor=0.5)


def test_strength_hand_check():
    r = tools.layer_shift_strength_check(**DEMO_SHIFT)
    # Intact: 500 N / 200 mm^2 = 2.5 MPa; allowable 50*0.5 = 25 MPa -> SF 10
    assert math.isclose(r["intact_safety_factor"], 10.0)
    # Shifted: A = 16*10 = 160, I = 10*16^3/12 = 3413.33, c = 8, M = 500*4/2 = 1000 N*mm
    hand = 500 / 160 + 1000 * 8 / (10 * 16**3 / 12)   # 3.125 + 2.34375 = 5.46875 MPa
    assert math.isclose(r["peak_stress_MPa"], hand, abs_tol=1e-3)
    assert math.isclose(r["safety_factor"], 25 / hand, abs_tol=1e-3)   # 4.571
    assert r["meets_requirement"] and math.isclose(r["area_retained_fraction"], 0.8)


def test_strength_no_shift_and_separated():
    intact = tools.layer_shift_strength_check(**{**DEMO_SHIFT, "shift_mm": 0})
    assert math.isclose(intact["safety_factor"], intact["intact_safety_factor"])
    sep = tools.layer_shift_strength_check(**{**DEMO_SHIFT, "shift_mm": 20})
    assert sep["safety_factor"] == 0 and sep["meets_requirement"] is False and sep["peak_stress_MPa"] is None


@pytest.mark.parametrize("override", [
    {"interlayer_strength_factor": 1.5},               # fraction above 1
    {"axial_force_N": 0, "bending_moment_Nmm": 0},      # no load
    {"tensile_strength_MPa": 0},                       # zero strength
])
def test_strength_invalid_inputs(override):
    with pytest.raises(ValueError):
        tools.layer_shift_strength_check(**{**DEMO_SHIFT, **override})


# ---------------------------------------------------------------- MCP server (in-process client)

async def _call(name, args):
    async with Client(mcp) as client:
        return await client.call_tool(name, args)


def test_server_lists_five_read_only_tools():
    async def go():
        async with Client(mcp) as client:
            return (await client.list_tools()).tools
    listed = asyncio.run(go())
    assert {t.name for t in listed} == {"check_functional_geometry", "check_recovery_feasibility",
                                        "expected_recovery_savings", "early_stop_trend_alarm",
                                        "layer_shift_strength_check"}
    for t in listed:
        assert t.annotations.read_only_hint is True and t.output_schema is not None


def test_server_structured_result():
    res = asyncio.run(_call("layer_shift_strength_check", DEMO_SHIFT))
    assert not res.is_error and math.isclose(res.structured_content["safety_factor"], 4.571)


def test_server_schema_rejection():
    res = asyncio.run(_call("expected_recovery_savings",
                            dict(restart_time_h=5, recovery_time_h=2, intervention_time_h=0.25,
                                 restart_filament_g=120, recovery_filament_g=50, success_probability=80)))
    assert res.is_error and "success_probability" in res.content[0].text


def test_server_domain_rejection_message_reaches_client():
    res = asyncio.run(_call("check_functional_geometry",
                            dict(outer_radius_mm=20, wall_thickness_mm=25, height_mm=50,
                                 base_thickness_mm=2, min_capacity_mL=45)))
    assert res.is_error and "wall thickness must be < outer radius" in res.content[0].text
