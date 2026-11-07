"""Analytical tools for the 3D Print Recovery Assistant.

Tools 1-3 are copied unchanged from Homework 4. Tools 4-5 are new in Homework 5.
Every function is pure Python (no network, no MCP dependency), validates its inputs,
and raises ValueError with a readable message on invalid input.
"""
import math


def _check(name, value, lo, hi):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not lo <= value <= hi:
        raise ValueError(f"{name} must be a number in [{lo}, {hi}], got {value!r}")


# ---------------------------------------------------------------- Homework 4 tools

def check_functional_geometry(outer_radius_mm: float, wall_thickness_mm: float, height_mm: float,
                              base_thickness_mm: float, min_capacity_mL: float) -> dict:
    '''Usable capacity of an open cylindrical container, V = pi*(r-t)^2*(H-b)/1000 mL,
    compared with a minimum required capacity. Capacity does not prove watertightness.'''
    _check("outer_radius_mm", outer_radius_mm, 1, 500)
    _check("wall_thickness_mm", wall_thickness_mm, 0.4, 50)
    _check("height_mm", height_mm, 1, 1000)
    _check("base_thickness_mm", base_thickness_mm, 0.2, 100)
    _check("min_capacity_mL", min_capacity_mL, 0, 1e6)
    if wall_thickness_mm >= outer_radius_mm or base_thickness_mm >= height_mm:
        raise ValueError("wall thickness must be < outer radius and base thickness must be < height")
    capacity = math.pi * (outer_radius_mm - wall_thickness_mm) ** 2 * (height_mm - base_thickness_mm) / 1000
    return {"estimated_capacity_mL": round(capacity, 3),
            "margin_mL": round(capacity - min_capacity_mL, 3),
            "meets_requirement": capacity >= min_capacity_mL}


def check_recovery_feasibility(correction_mm: float, max_correction_per_layer_mm: float,
                               remaining_layers: int, layer_height_mm: float) -> dict:
    '''Whether a lateral contour correction can be spread over the remaining layers without exceeding
    an ASSUMED per-layer limit. Required layers = ceil(correction / limit).'''
    _check("correction_mm", correction_mm, 0, 50)
    _check("max_correction_per_layer_mm", max_correction_per_layer_mm, 0.01, 2)
    _check("remaining_layers", remaining_layers, 0, 100_000)
    _check("layer_height_mm", layer_height_mm, 0.04, 1.0)
    if remaining_layers != int(remaining_layers):
        raise ValueError(f"remaining_layers must be a whole number, got {remaining_layers}")
    # round() guards against float artifacts such as 1.1/0.1 = 11.000000000000002
    required = math.ceil(round(correction_mm / max_correction_per_layer_mm, 9))
    return {"required_layers": required,
            "transition_height_mm": round(required * layer_height_mm, 3),
            "spare_layers": int(remaining_layers) - required,
            "feasible": required <= remaining_layers}


def expected_recovery_savings(restart_time_h: float, recovery_time_h: float, intervention_time_h: float,
                              restart_filament_g: float, recovery_filament_g: float,
                              success_probability: float) -> dict:
    '''Expected time and filament savings of attempting recovery instead of restarting.
    E[T] = intervention + recovery + (1-p)*restart; E[F] = recovery + (1-p)*restart filament.'''
    _check("restart_time_h", restart_time_h, 0.01, 1000)
    _check("recovery_time_h", recovery_time_h, 0, 1000)
    _check("intervention_time_h", intervention_time_h, 0, 100)
    _check("restart_filament_g", restart_filament_g, 0.1, 1e5)
    _check("recovery_filament_g", recovery_filament_g, 0, 1e5)
    _check("success_probability", success_probability, 0, 1)
    fail = 1 - success_probability
    exp_time = intervention_time_h + recovery_time_h + fail * restart_time_h
    exp_filament = recovery_filament_g + fail * restart_filament_g
    return {"expected_recovery_time_h": round(exp_time, 3),
            "expected_time_savings_h": round(restart_time_h - exp_time, 3),
            "expected_recovery_filament_g": round(exp_filament, 3),
            "expected_filament_savings_g": round(restart_filament_g - exp_filament, 3),
            "breakeven_probability_time": round((intervention_time_h + recovery_time_h) / restart_time_h, 3)}


# ---------------------------------------------------------------- New in Homework 5

def early_stop_trend_alarm(layer_numbers: list, deviations_mm: list, tolerance_mm: float,
                           total_layers: int, watch_fraction: float = 0.5,
                           total_print_time_h: float | None = None,
                           total_filament_g: float | None = None) -> dict:
    '''Graded early warning (OK / WATCH / STOP) from deviations measured during a print.

    Fits a least-squares line d(n) = a + b*n to the measured deviation magnitudes and projects it
    to the final layer. STOP if the latest deviation already exceeds the tolerance or the trend
    reaches it before the print ends; WATCH if either reaches watch_fraction * tolerance.
    If print time and filament are given, also reports what stopping now would save, assuming
    time and filament are spread evenly over layers.'''
    if not isinstance(layer_numbers, list) or not isinstance(deviations_mm, list):
        raise ValueError("layer_numbers and deviations_mm must be lists")
    if len(layer_numbers) != len(deviations_mm):
        raise ValueError(f"layer_numbers ({len(layer_numbers)}) and deviations_mm "
                         f"({len(deviations_mm)}) must have the same length")
    if not 3 <= len(layer_numbers) <= 10_000:
        raise ValueError(f"need between 3 and 10000 measurements to fit a trend, got {len(layer_numbers)}")
    for n in layer_numbers:
        _check("each layer number", n, 0, 100_000)
        if n != int(n):
            raise ValueError(f"layer numbers must be whole numbers, got {n}")
    for d in deviations_mm:
        _check("each deviation_mm", d, 0, 50)
    if any(b <= a for a, b in zip(layer_numbers, layer_numbers[1:])):
        raise ValueError("layer_numbers must be strictly increasing")
    _check("tolerance_mm", tolerance_mm, 0.01, 50)
    _check("total_layers", total_layers, 1, 100_000)
    if total_layers != int(total_layers):
        raise ValueError(f"total_layers must be a whole number, got {total_layers}")
    if layer_numbers[-1] > total_layers:
        raise ValueError(f"last measured layer ({layer_numbers[-1]}) exceeds total_layers ({total_layers})")
    _check("watch_fraction", watch_fraction, 0.1, 0.99)
    if total_print_time_h is not None:
        _check("total_print_time_h", total_print_time_h, 0.01, 1000)
    if total_filament_g is not None:
        _check("total_filament_g", total_filament_g, 0.1, 1e5)

    k = len(layer_numbers)
    mean_n = sum(layer_numbers) / k
    mean_d = sum(deviations_mm) / k
    s_nn = sum((n - mean_n) ** 2 for n in layer_numbers)
    s_nd = sum((n - mean_n) * (d - mean_d) for n, d in zip(layer_numbers, deviations_mm))
    s_dd = sum((d - mean_d) ** 2 for d in deviations_mm)
    slope = s_nd / s_nn
    intercept = mean_d - slope * mean_n
    r_squared = 1.0 if s_dd == 0 else s_nd ** 2 / (s_nn * s_dd)

    current_layer = int(layer_numbers[-1])
    current_dev = deviations_mm[-1]
    projected_final = max(0.0, intercept + slope * total_layers)
    watch_level = watch_fraction * tolerance_mm

    exceed_layer = None
    if current_dev >= tolerance_mm:
        exceed_layer = current_layer
    elif slope > 0:
        n_star = math.ceil(round((tolerance_mm - intercept) / slope, 9))
        if n_star <= total_layers:
            exceed_layer = max(n_star, current_layer)

    if current_dev >= tolerance_mm or projected_final >= tolerance_mm:
        alert = "STOP"
    elif current_dev >= watch_level or projected_final >= watch_level:
        alert = "WATCH"
    else:
        alert = "OK"

    remaining_fraction = (total_layers - current_layer) / total_layers
    return {"alert_level": alert,
            "trend_slope_mm_per_layer": round(slope, 6),
            "trend_r_squared": round(r_squared, 3),
            "current_layer": current_layer,
            "current_deviation_mm": round(current_dev, 4),
            "projected_final_deviation_mm": round(projected_final, 4),
            "projected_exceedance_layer": exceed_layer,
            "layers_until_exceedance": None if exceed_layer is None else exceed_layer - current_layer,
            "remaining_fraction_of_print": round(remaining_fraction, 4),
            "time_saved_if_stopped_now_h": (None if total_print_time_h is None
                                            else round(remaining_fraction * total_print_time_h, 3)),
            "filament_saved_if_stopped_now_g": (None if total_filament_g is None
                                                else round(remaining_fraction * total_filament_g, 3))}


def layer_shift_strength_check(section_width_mm: float, section_depth_mm: float, shift_mm: float,
                               axial_force_N: float, bending_moment_Nmm: float,
                               tensile_strength_MPa: float, interlayer_strength_factor: float,
                               required_safety_factor: float = 2.0) -> dict:
    '''Strength of a rectangular section across a layer-shift interface, loaded in Z.

    A shift s along the width leaves a bonded overlap of (W - s) x D. The load line stays at the
    centre of the upper part, so the shift adds an eccentric moment F*s/2 about the overlap centroid.
    Peak stress = F/A + (M + F*s/2) * c / I with A = (W-s)D, I = D(W-s)^3/12, c = (W-s)/2.
    Allowable stress = tensile_strength * interlayer_strength_factor. Compared with an unshifted
    section to show how much strength the shift costs.'''
    _check("section_width_mm", section_width_mm, 1, 500)
    _check("section_depth_mm", section_depth_mm, 1, 500)
    _check("shift_mm", shift_mm, 0, 500)
    _check("axial_force_N", axial_force_N, 0, 1e5)
    _check("bending_moment_Nmm", bending_moment_Nmm, 0, 1e8)
    _check("tensile_strength_MPa", tensile_strength_MPa, 1, 200)
    _check("interlayer_strength_factor", interlayer_strength_factor, 0.05, 1.0)
    _check("required_safety_factor", required_safety_factor, 1, 20)
    if axial_force_N == 0 and bending_moment_Nmm == 0:
        raise ValueError("at least one of axial_force_N or bending_moment_Nmm must be positive")

    allowable = tensile_strength_MPa * interlayer_strength_factor

    def peak_stress(width, eccentric_shift):
        area = width * section_depth_mm
        inertia = section_depth_mm * width ** 3 / 12
        moment = bending_moment_Nmm + axial_force_N * eccentric_shift / 2
        return axial_force_N / area + moment * (width / 2) / inertia

    intact = peak_stress(section_width_mm, 0)
    overlap = section_width_mm - shift_mm
    if overlap <= 0:
        return {"bonded_area_mm2": 0.0, "area_retained_fraction": 0.0,
                "peak_stress_MPa": None, "allowable_stress_MPa": round(allowable, 3),
                "safety_factor": 0.0, "intact_safety_factor": round(allowable / intact, 3),
                "strength_retained_fraction": 0.0, "meets_requirement": False,
                "note": "shift is at least the section width: no bonded overlap, the part is separated"}
    stress = peak_stress(overlap, shift_mm)
    sf = allowable / stress
    return {"bonded_area_mm2": round(overlap * section_depth_mm, 3),
            "area_retained_fraction": round(overlap / section_width_mm, 4),
            "peak_stress_MPa": round(stress, 3),
            "allowable_stress_MPa": round(allowable, 3),
            "safety_factor": round(sf, 3),
            "intact_safety_factor": round(allowable / intact, 3),
            "strength_retained_fraction": round(intact / stress, 4),
            "meets_requirement": sf >= required_safety_factor,
            "note": None}
