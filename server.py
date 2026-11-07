"""MCP server for the 3D Print Recovery Assistant (CMU 24-679 HW5, Question 4).

Exposes five read-only analytical tools over stdio. Each tool's input schema carries units and
valid ranges, each returns a typed structured result, and invalid inputs come back as an MCP tool
error (isError: true) with a readable reason. The server makes no network calls and never sends
commands to a printer: it only computes. Deciding what to do with a result is left to the client
and the human.

Run:  python server.py            (stdio transport, for Claude Code / Claude Desktop / Inspector)
"""
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp_types import ToolAnnotations
from pydantic import BaseModel, Field

import tools

mcp = MCPServer(
    name="print-recovery",
    title="3D Print Recovery Assistant",
    version="1.0.0",
    instructions=(
        "Analytical tools for deciding what to do about a failing or failed FDM 3D print. "
        "All inputs use the units in their names (mm, h, g, N, MPa); convert before calling "
        "(minutes -> hours, percent -> fraction, diameter -> radius). Never invent missing inputs; "
        "ask the user. These tools only compute: they never change printer settings, and every "
        "result should be shown to the user with its limitation before they act on it."),
)

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False,
                            idempotent_hint=True, open_world_hint=False)


def _run(fn, **kwargs):
    """Call a tool function and turn domain-rule violations into MCP tool errors."""
    try:
        return fn(**kwargs)
    except ValueError as e:
        # ToolError (unlike a bare exception) passes its message through to the client.
        raise ToolError(f"Invalid input: {e}") from e


# ---------------------------------------------------------------- result models

class GeometryResult(BaseModel):
    estimated_capacity_mL: float = Field(description="Usable capacity, mL")
    margin_mL: float = Field(description="Capacity minus requirement, mL (negative = short)")
    meets_requirement: bool


class FeasibilityResult(BaseModel):
    required_layers: int = Field(description="Layers needed to spread the correction")
    transition_height_mm: float = Field(description="Height of the transition zone, mm")
    spare_layers: int = Field(description="Remaining layers minus required (negative = infeasible)")
    feasible: bool


class SavingsResult(BaseModel):
    expected_recovery_time_h: float = Field(description="Expected total time if recovery is attempted, h")
    expected_time_savings_h: float = Field(description="Restart time minus expected recovery time, h")
    expected_recovery_filament_g: float = Field(description="Expected filament if recovery is attempted, g")
    expected_filament_savings_g: float = Field(description="Restart filament minus expected recovery filament, g")
    breakeven_probability_time: float = Field(description="Success probability above which recovery saves time")


class TrendAlarmResult(BaseModel):
    alert_level: str = Field(description="OK, WATCH or STOP")
    trend_slope_mm_per_layer: float = Field(description="Fitted growth of deviation, mm/layer")
    trend_r_squared: float = Field(description="Fit quality 0-1; low values mean the trend is unreliable")
    current_layer: int
    current_deviation_mm: float
    projected_final_deviation_mm: float = Field(description="Trend extrapolated to the last layer, mm")
    projected_exceedance_layer: int | None = Field(description="Layer where tolerance is reached; null if never")
    layers_until_exceedance: int | None
    remaining_fraction_of_print: float = Field(description="Fraction of layers not yet printed")
    time_saved_if_stopped_now_h: float | None = Field(description="Null if total_print_time_h not given")
    filament_saved_if_stopped_now_g: float | None = Field(description="Null if total_filament_g not given")


class StrengthResult(BaseModel):
    bonded_area_mm2: float = Field(description="Overlap area across the shifted interface, mm^2")
    area_retained_fraction: float
    peak_stress_MPa: float | None = Field(description="Axial + bending stress at the interface; null if separated")
    allowable_stress_MPa: float = Field(description="tensile_strength x interlayer_strength_factor, MPa")
    safety_factor: float
    intact_safety_factor: float = Field(description="Safety factor of the same section with no shift")
    strength_retained_fraction: float = Field(description="Intact peak stress / shifted peak stress")
    meets_requirement: bool = Field(description="safety_factor >= required_safety_factor")
    note: str | None


# ---------------------------------------------------------------- tools 1-3 (Homework 4)

@mcp.tool(title="Functional geometry checker (HW4 Tool 1)", annotations=READ_ONLY)
def check_functional_geometry(
    outer_radius_mm: Annotated[float, Field(ge=1, le=500, description="Outer radius, mm (diameter/2)")],
    wall_thickness_mm: Annotated[float, Field(ge=0.4, le=50, description="Wall thickness, mm; must be < radius")],
    height_mm: Annotated[float, Field(ge=1, le=1000, description="Total outer height, mm")],
    base_thickness_mm: Annotated[float, Field(ge=0.2, le=100, description="Base thickness, mm; must be < height")],
    min_capacity_mL: Annotated[float, Field(ge=0, le=1e6, description="Minimum required capacity, mL")],
) -> GeometryResult:
    """Usable capacity of an open cylindrical container, V = pi*(r-t)^2*(H-b)/1000 mL, compared with a
    required capacity. Assumes an ideal cylinder filled to the brim. Does NOT prove watertightness."""
    return GeometryResult(**_run(tools.check_functional_geometry, **locals()))


@mcp.tool(title="Geometric recovery feasibility (HW4 Tool 2)", annotations=READ_ONLY)
def check_recovery_feasibility(
    correction_mm: Annotated[float, Field(ge=0, le=50, description="Lateral contour correction needed, mm")],
    max_correction_per_layer_mm: Annotated[float, Field(ge=0.01, le=2, description="Assumed max correction per layer, mm/layer")],
    remaining_layers: Annotated[int, Field(ge=0, le=100_000, description="Layers left in the print")],
    layer_height_mm: Annotated[float, Field(ge=0.04, le=1.0, description="Layer height, mm")],
) -> FeasibilityResult:
    """Whether a correction can be spread over the remaining layers without exceeding an ASSUMED per-layer
    limit: required layers = ceil(correction / limit). Does not guarantee strength, nozzle clearance or
    print success."""
    return FeasibilityResult(**_run(tools.check_recovery_feasibility, **locals()))


@mcp.tool(title="Expected recovery savings (HW4 Tool 3)", annotations=READ_ONLY)
def expected_recovery_savings(
    restart_time_h: Annotated[float, Field(ge=0.01, le=1000, description="Time to reprint from scratch, h")],
    recovery_time_h: Annotated[float, Field(ge=0, le=1000, description="Print time of the recovery attempt, h")],
    intervention_time_h: Annotated[float, Field(ge=0, le=100, description="Human intervention time, h (15 min = 0.25)")],
    restart_filament_g: Annotated[float, Field(ge=0.1, le=1e5, description="Filament for a full restart, g")],
    recovery_filament_g: Annotated[float, Field(ge=0, le=1e5, description="Filament for the recovery attempt, g")],
    success_probability: Annotated[float, Field(ge=0, le=1, description="Probability recovery succeeds, 0-1 (80% = 0.8)")],
) -> SavingsResult:
    """Expected time and filament savings of attempting recovery instead of restarting, with the
    break-even success probability. Risk-neutral, single attempt; p is supplied by the user, not learned."""
    return SavingsResult(**_run(tools.expected_recovery_savings, **locals()))


# ---------------------------------------------------------------- tools 4-5 (new in HW5)

@mcp.tool(title="Early-stop trend alarm (new)", annotations=READ_ONLY)
def early_stop_trend_alarm(
    layer_numbers: Annotated[list[int], Field(min_length=3, max_length=10_000,
                                              description="Layers at which deviation was measured, strictly increasing, 0-100000")],
    deviations_mm: Annotated[list[float], Field(min_length=3, max_length=10_000,
                                                description="Measured deviation magnitude at each layer (warp lift, shift, under-extrusion width), mm, 0-50")],
    tolerance_mm: Annotated[float, Field(ge=0.01, le=50, description="Functional tolerance for this deviation, mm")],
    total_layers: Annotated[int, Field(ge=1, le=100_000, description="Total layers in the print")],
    watch_fraction: Annotated[float, Field(ge=0.1, le=0.99, description="Fraction of tolerance that triggers WATCH")] = 0.5,
    total_print_time_h: Annotated[float | None, Field(ge=0.01, le=1000, description="Optional total print time, h")] = None,
    total_filament_g: Annotated[float | None, Field(ge=0.1, le=1e5, description="Optional total filament, g")] = None,
) -> TrendAlarmResult:
    """Graded early warning (OK / WATCH / STOP) while a print is running. Fits a line to measured
    deviation vs layer and projects it to the last layer. STOP if the deviation already exceeds the
    tolerance or is projected to before the print ends; WATCH if it reaches watch_fraction of it.
    Reports how much time and filament stopping now would save. Linear extrapolation only: check
    trend_r_squared, and confirm the defect on the printer before stopping."""
    return TrendAlarmResult(**_run(tools.early_stop_trend_alarm, **locals()))


@mcp.tool(title="Layer-shift strength check (new)", annotations=READ_ONLY)
def layer_shift_strength_check(
    section_width_mm: Annotated[float, Field(ge=1, le=500, description="Section width along the shift direction, mm")],
    section_depth_mm: Annotated[float, Field(ge=1, le=500, description="Section depth perpendicular to the shift, mm")],
    shift_mm: Annotated[float, Field(ge=0, le=500, description="Measured layer-shift offset, mm")],
    axial_force_N: Annotated[float, Field(ge=0, le=1e5, description="Tensile force across the layers (Z), N")],
    bending_moment_Nmm: Annotated[float, Field(ge=0, le=1e8, description="Applied bending moment about the depth axis, N*mm")],
    tensile_strength_MPa: Annotated[float, Field(ge=1, le=200, description="Material tensile strength from the datasheet, MPa")],
    interlayer_strength_factor: Annotated[float, Field(ge=0.05, le=1.0, description="Z-direction strength as a fraction of tensile strength, 0.05-1")],
    required_safety_factor: Annotated[float, Field(ge=1, le=20, description="Minimum acceptable safety factor")] = 2.0,
) -> StrengthResult:
    """Whether a part with a layer shift still carries its load. A shift s leaves a bonded overlap of
    (W - s) x D and adds an eccentric moment F*s/2. Peak stress = F/A + (M + F*s/2)*c/I, compared
    with tensile_strength x interlayer_strength_factor and with the unshifted section. Simple beam
    theory on a solid rectangle: ignores infill, stress concentration at the step and fatigue."""
    return StrengthResult(**_run(tools.layer_shift_strength_check, **locals()))


if __name__ == "__main__":
    mcp.run()
