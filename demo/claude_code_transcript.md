# Claude Code demo transcript

Recorded 2026-11-07 with Claude Code CLI 1.0.93 in headless mode (`claude -p --model claude-sonnet-5-5 --output-format stream-json`), connected to this server over stdio with `--mcp-config` and `--strict-mcp-config` (no other MCP servers). Only the five print-recovery tools were allowed. Internal to-do-list calls are omitted; every MCP tool call and server result is shown verbatim.

## Request 1: "A print of a robot sensor bracket shows a 4 mm layer shift. The section at the shift is 20 mm wide (along the shift) and 10 mm deep, and it carries 500 N of tension across the layers with no bending. The PLA datasheet says 50 MPa tensile strength and I assume interlayer strength is 50% of that. I need a safety factor of at least 2. Is the part still strong enough, and how much strength did the shift cost?"

Connected MCP servers: `[{'name': 'print-recovery', 'status': 'connected'}]`  
Model: `claude-sonnet-5-5`

**Tool call:** `mcp__print-recovery__layer_shift_strength_check`

```json
{
  "section_width_mm": 20,
  "section_depth_mm": 10,
  "shift_mm": 4,
  "axial_force_N": 500,
  "bending_moment_Nmm": 0,
  "tensile_strength_MPa": 50,
  "interlayer_strength_factor": 0.5,
  "required_safety_factor": 2
}
```

**Server result** (is_error=False):

```json
{
  "bonded_area_mm2": 160.0,
  "area_retained_fraction": 0.8,
  "peak_stress_MPa": 5.469,
  "allowable_stress_MPa": 25.0,
  "safety_factor": 4.571,
  "intact_safety_factor": 10.0,
  "strength_retained_fraction": 0.4571,
  "meets_requirement": true,
  "note": null
}
```

**Claude:**

**Yes, it passes.** The safety factor is 4.57 against your requirement of 2.

| | Shifted | Unshifted |
|---|---|---|
| Bonded area | 160 mm² (80% of 200) | 200 mm² |
| Peak stress | 5.47 MPa | 2.5 MPa |
| Allowable stress (50 MPa × 0.5) | 25 MPa | 25 MPa |
| Safety factor | 4.57 | 10.0 |

**Cost of the shift:** the part keeps about 46% of its safety margin, so it lost about 54%. The area loss is only 20%. The rest comes from the eccentric moment (F·s/2 = 1000 N·mm) that the offset adds, which pushes peak stress up from 3.1 MPa (500 N over 160 mm²) to 5.47 MPa.

**Limitations of this check:**
- It uses simple beam theory on a solid rectangle. It ignores infill, which could lower the real capacity if the part is not 100% infill.
- It ignores stress concentration at the step, which is likely significant for a sharp 4 mm offset.
- It ignores fatigue, which matters if the bracket sees vibration or cyclic loads on the robot.
- The 50% interlayer factor is your assumption. If the true value is lower, for example 25%, the allowable stress halves and the safety factor falls to about 2.3, close to your limit.

Before you rely on the part, I'd print a test coupon with the same shift and pull it, or confirm the interlayer factor for your PLA and print settings.


## Request 2: "My overnight print is 200 layers, 480 minutes and 150 g total. The camera measured corner warp lift of 0.05, 0.10, 0.16, 0.21 and 0.25 mm at layers 10, 20, 30, 40 and 50. The part stops fitting its mount if warp exceeds 0.5 mm. Should I stop it now?" (note the client converts 480 min to 8 h)

Connected MCP servers: `[{'name': 'print-recovery', 'status': 'connected'}]`  
Model: `claude-sonnet-5-5`

**Tool call:** `mcp__print-recovery__early_stop_trend_alarm`

```json
{
  "layer_numbers": [
    10,
    20,
    30,
    40,
    50
  ],
  "deviations_mm": [
    0.05,
    0.1,
    0.16,
    0.21,
    0.25
  ],
  "tolerance_mm": 0.5,
  "total_layers": 200,
  "total_filament_g": 150,
  "total_print_time_h": 8
}
```

**Server result** (is_error=False):

```json
{
  "alert_level": "STOP",
  "trend_slope_mm_per_layer": 0.0051,
  "trend_r_squared": 0.996,
  "current_layer": 50,
  "current_deviation_mm": 0.25,
  "projected_final_deviation_mm": 1.021,
  "projected_exceedance_layer": 98,
  "layers_until_exceedance": 48,
  "remaining_fraction_of_print": 0.75,
  "time_saved_if_stopped_now_h": 6.0,
  "filament_saved_if_stopped_now_g": 112.5
}
```

**Claude:**

**The tool says STOP.** Stopping now would save about 6 h and 112.5 g.

- **Trend:** warp is growing about 0.0051 mm per layer. The linear fit is very good (R² = 0.996).
- **Projection:** warp reaches about 1.02 mm at layer 200. That is roughly twice your 0.5 mm limit.
- **When it fails:** warp is projected to cross 0.5 mm at layer 98, which is 48 layers from now. After that the part won't fit its mount.

**Limitations:**
- This is a straight-line extrapolation. Warp can level off as the part gets taller, or it can speed up. A fit this clean on 5 points still doesn't guarantee the trend continues.
- Before you cancel, look at the corners on the printer. If they are visibly lifting, stop.
- If you'd like to try saving the print, I can run the recovery-savings tool. For that I need your estimates of the recovery time and filament, the time you'd spend intervening, and your guess at the chance it works.
- Whatever you decide, fix the cause before reprinting. Options are a hotter bed, a brim, an enclosure, or better bed adhesion. Otherwise the restart will probably warp the same way.

