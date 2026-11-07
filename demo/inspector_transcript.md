# MCP Inspector demo transcript

Recorded 2026-11-07 16:38 EST with `@modelcontextprotocol/inspector` (CLI mode) over stdio.
Server: `print-recovery` v1.0.0, MCP Python SDK 2.3.0.

## 1. List tools (full input and output schemas)

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/list
```

```json
{
  "tools": [
    {
      "name": "check_functional_geometry",
      "title": "Functional geometry checker (HW4 Tool 1)",
      "description": "Usable capacity of an open cylindrical container, V = pi*(r-t)^2*(H-b)/1000 mL, compared with a\n    required capacity. Assumes an ideal cylinder filled to the brim. Does NOT prove watertightness.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "outer_radius_mm": {
            "description": "Outer radius, mm (diameter/2)",
            "maximum": 500,
            "minimum": 1,
            "title": "Outer Radius Mm",
            "type": "number"
          },
          "wall_thickness_mm": {
            "description": "Wall thickness, mm; must be < radius",
            "maximum": 50,
            "minimum": 0.4,
            "title": "Wall Thickness Mm",
            "type": "number"
          },
          "height_mm": {
            "description": "Total outer height, mm",
            "maximum": 1000,
            "minimum": 1,
            "title": "Height Mm",
            "type": "number"
          },
          "base_thickness_mm": {
            "description": "Base thickness, mm; must be < height",
            "maximum": 100,
            "minimum": 0.2,
            "title": "Base Thickness Mm",
            "type": "number"
          },
          "min_capacity_mL": {
            "description": "Minimum required capacity, mL",
            "maximum": 1000000,
            "minimum": 0,
            "title": "Min Capacity Ml",
            "type": "number"
          }
        },
        "required": [
          "outer_radius_mm",
          "wall_thickness_mm",
          "height_mm",
          "base_thickness_mm",
          "min_capacity_mL"
        ],
        "title": "check_functional_geometryArguments"
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "estimated_capacity_mL": {
            "description": "Usable capacity, mL",
            "title": "Estimated Capacity Ml",
            "type": "number"
          },
          "margin_mL": {
            "description": "Capacity minus requirement, mL (negative = short)",
            "title": "Margin Ml",
            "type": "number"
          },
          "meets_requirement": {
            "title": "Meets Requirement",
            "type": "boolean"
          }
        },
        "required": [
          "estimated_capacity_mL",
          "margin_mL",
          "meets_requirement"
        ],
        "title": "GeometryResult"
      },
      "annotations": {
        "readOnlyHint": true,
        "destructiveHint": false,
        "idempotentHint": true,
        "openWorldHint": false
      }
    },
    {
      "name": "check_recovery_feasibility",
      "title": "Geometric recovery feasibility (HW4 Tool 2)",
      "description": "Whether a correction can be spread over the remaining layers without exceeding an ASSUMED per-layer\n    limit: required layers = ceil(correction / limit). Does not guarantee strength, nozzle clearance or\n    print success.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "correction_mm": {
            "description": "Lateral contour correction needed, mm",
            "maximum": 50,
            "minimum": 0,
            "title": "Correction Mm",
            "type": "number"
          },
          "max_correction_per_layer_mm": {
            "description": "Assumed max correction per layer, mm/layer",
            "maximum": 2,
            "minimum": 0.01,
            "title": "Max Correction Per Layer Mm",
            "type": "number"
          },
          "remaining_layers": {
            "description": "Layers left in the print",
            "maximum": 100000,
            "minimum": 0,
            "title": "Remaining Layers",
            "type": "integer"
          },
          "layer_height_mm": {
            "description": "Layer height, mm",
            "maximum": 1,
            "minimum": 0.04,
            "title": "Layer Height Mm",
            "type": "number"
          }
        },
        "required": [
          "correction_mm",
          "max_correction_per_layer_mm",
          "remaining_layers",
          "layer_height_mm"
        ],
        "title": "check_recovery_feasibilityArguments"
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "required_layers": {
            "description": "Layers needed to spread the correction",
            "title": "Required Layers",
            "type": "integer"
          },
          "transition_height_mm": {
            "description": "Height of the transition zone, mm",
            "title": "Transition Height Mm",
            "type": "number"
          },
          "spare_layers": {
            "description": "Remaining layers minus required (negative = infeasible)",
            "title": "Spare Layers",
            "type": "integer"
          },
          "feasible": {
            "title": "Feasible",
            "type": "boolean"
          }
        },
        "required": [
          "required_layers",
          "transition_height_mm",
          "spare_layers",
          "feasible"
        ],
        "title": "FeasibilityResult"
      },
      "annotations": {
        "readOnlyHint": true,
        "destructiveHint": false,
        "idempotentHint": true,
        "openWorldHint": false
      }
    },
    {
      "name": "expected_recovery_savings",
      "title": "Expected recovery savings (HW4 Tool 3)",
      "description": "Expected time and filament savings of attempting recovery instead of restarting, with the\n    break-even success probability. Risk-neutral, single attempt; p is supplied by the user, not learned.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "restart_time_h": {
            "description": "Time to reprint from scratch, h",
            "maximum": 1000,
            "minimum": 0.01,
            "title": "Restart Time H",
            "type": "number"
          },
          "recovery_time_h": {
            "description": "Print time of the recovery attempt, h",
            "maximum": 1000,
            "minimum": 0,
            "title": "Recovery Time H",
            "type": "number"
          },
          "intervention_time_h": {
            "description": "Human intervention time, h (15 min = 0.25)",
            "maximum": 100,
            "minimum": 0,
            "title": "Intervention Time H",
            "type": "number"
          },
          "restart_filament_g": {
            "description": "Filament for a full restart, g",
            "maximum": 100000,
            "minimum": 0.1,
            "title": "Restart Filament G",
            "type": "number"
          },
          "recovery_filament_g": {
            "description": "Filament for the recovery attempt, g",
            "maximum": 100000,
            "minimum": 0,
            "title": "Recovery Filament G",
            "type": "number"
          },
          "success_probability": {
            "description": "Probability recovery succeeds, 0-1 (80% = 0.8)",
            "maximum": 1,
            "minimum": 0,
            "title": "Success Probability",
            "type": "number"
          }
        },
        "required": [
          "restart_time_h",
          "recovery_time_h",
          "intervention_time_h",
          "restart_filament_g",
          "recovery_filament_g",
          "success_probability"
        ],
        "title": "expected_recovery_savingsArguments"
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "expected_recovery_time_h": {
            "description": "Expected total time if recovery is attempted, h",
            "title": "Expected Recovery Time H",
            "type": "number"
          },
          "expected_time_savings_h": {
            "description": "Restart time minus expected recovery time, h",
            "title": "Expected Time Savings H",
            "type": "number"
          },
          "expected_recovery_filament_g": {
            "description": "Expected filament if recovery is attempted, g",
            "title": "Expected Recovery Filament G",
            "type": "number"
          },
          "expected_filament_savings_g": {
            "description": "Restart filament minus expected recovery filament, g",
            "title": "Expected Filament Savings G",
            "type": "number"
          },
          "breakeven_probability_time": {
            "description": "Success probability above which recovery saves time",
            "title": "Breakeven Probability Time",
            "type": "number"
          }
        },
        "required": [
          "expected_recovery_time_h",
          "expected_time_savings_h",
          "expected_recovery_filament_g",
          "expected_filament_savings_g",
          "breakeven_probability_time"
        ],
        "title": "SavingsResult"
      },
      "annotations": {
        "readOnlyHint": true,
        "destructiveHint": false,
        "idempotentHint": true,
        "openWorldHint": false
      }
    },
    {
      "name": "early_stop_trend_alarm",
      "title": "Early-stop trend alarm (new)",
      "description": "Graded early warning (OK / WATCH / STOP) while a print is running. Fits a line to measured\n    deviation vs layer and projects it to the last layer. STOP if the deviation already exceeds the\n    tolerance or is projected to before the print ends; WATCH if it reaches watch_fraction of it.\n    Reports how much time and filament stopping now would save. Linear extrapolation only: check\n    trend_r_squared, and confirm the defect on the printer before stopping.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "layer_numbers": {
            "description": "Layers at which deviation was measured, strictly increasing, 0-100000",
            "items": {
              "type": "integer"
            },
            "maxItems": 10000,
            "minItems": 3,
            "title": "Layer Numbers",
            "type": "array"
          },
          "deviations_mm": {
            "description": "Measured deviation magnitude at each layer (warp lift, shift, under-extrusion width), mm, 0-50",
            "items": {
              "type": "number"
            },
            "maxItems": 10000,
            "minItems": 3,
            "title": "Deviations Mm",
            "type": "array"
          },
          "tolerance_mm": {
            "description": "Functional tolerance for this deviation, mm",
            "maximum": 50,
            "minimum": 0.01,
            "title": "Tolerance Mm",
            "type": "number"
          },
          "total_layers": {
            "description": "Total layers in the print",
            "maximum": 100000,
            "minimum": 1,
            "title": "Total Layers",
            "type": "integer"
          },
          "watch_fraction": {
            "default": 0.5,
            "description": "Fraction of tolerance that triggers WATCH",
            "maximum": 0.99,
            "minimum": 0.1,
            "title": "Watch Fraction",
            "type": "number"
          },
          "total_print_time_h": {
            "anyOf": [
              {
                "maximum": 1000,
                "minimum": 0.01,
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Optional total print time, h",
            "title": "Total Print Time H"
          },
          "total_filament_g": {
            "anyOf": [
              {
                "maximum": 100000,
                "minimum": 0.1,
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "default": null,
            "description": "Optional total filament, g",
            "title": "Total Filament G"
          }
        },
        "required": [
          "layer_numbers",
          "deviations_mm",
          "tolerance_mm",
          "total_layers"
        ],
        "title": "early_stop_trend_alarmArguments"
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "alert_level": {
            "description": "OK, WATCH or STOP",
            "title": "Alert Level",
            "type": "string"
          },
          "trend_slope_mm_per_layer": {
            "description": "Fitted growth of deviation, mm/layer",
            "title": "Trend Slope Mm Per Layer",
            "type": "number"
          },
          "trend_r_squared": {
            "description": "Fit quality 0-1; low values mean the trend is unreliable",
            "title": "Trend R Squared",
            "type": "number"
          },
          "current_layer": {
            "title": "Current Layer",
            "type": "integer"
          },
          "current_deviation_mm": {
            "title": "Current Deviation Mm",
            "type": "number"
          },
          "projected_final_deviation_mm": {
            "description": "Trend extrapolated to the last layer, mm",
            "title": "Projected Final Deviation Mm",
            "type": "number"
          },
          "projected_exceedance_layer": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "description": "Layer where tolerance is reached; null if never",
            "title": "Projected Exceedance Layer"
          },
          "layers_until_exceedance": {
            "anyOf": [
              {
                "type": "integer"
              },
              {
                "type": "null"
              }
            ],
            "title": "Layers Until Exceedance"
          },
          "remaining_fraction_of_print": {
            "description": "Fraction of layers not yet printed",
            "title": "Remaining Fraction Of Print",
            "type": "number"
          },
          "time_saved_if_stopped_now_h": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "description": "Null if total_print_time_h not given",
            "title": "Time Saved If Stopped Now H"
          },
          "filament_saved_if_stopped_now_g": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "description": "Null if total_filament_g not given",
            "title": "Filament Saved If Stopped Now G"
          }
        },
        "required": [
          "alert_level",
          "trend_slope_mm_per_layer",
          "trend_r_squared",
          "current_layer",
          "current_deviation_mm",
          "projected_final_deviation_mm",
          "projected_exceedance_layer",
          "layers_until_exceedance",
          "remaining_fraction_of_print",
          "time_saved_if_stopped_now_h",
          "filament_saved_if_stopped_now_g"
        ],
        "title": "TrendAlarmResult"
      },
      "annotations": {
        "readOnlyHint": true,
        "destructiveHint": false,
        "idempotentHint": true,
        "openWorldHint": false
      }
    },
    {
      "name": "layer_shift_strength_check",
      "title": "Layer-shift strength check (new)",
      "description": "Whether a part with a layer shift still carries its load. A shift s leaves a bonded overlap of\n    (W - s) x D and adds an eccentric moment F*s/2. Peak stress = F/A + (M + F*s/2)*c/I, compared\n    with tensile_strength x interlayer_strength_factor and with the unshifted section. Simple beam\n    theory on a solid rectangle: ignores infill, stress concentration at the step and fatigue.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "section_width_mm": {
            "description": "Section width along the shift direction, mm",
            "maximum": 500,
            "minimum": 1,
            "title": "Section Width Mm",
            "type": "number"
          },
          "section_depth_mm": {
            "description": "Section depth perpendicular to the shift, mm",
            "maximum": 500,
            "minimum": 1,
            "title": "Section Depth Mm",
            "type": "number"
          },
          "shift_mm": {
            "description": "Measured layer-shift offset, mm",
            "maximum": 500,
            "minimum": 0,
            "title": "Shift Mm",
            "type": "number"
          },
          "axial_force_N": {
            "description": "Tensile force across the layers (Z), N",
            "maximum": 100000,
            "minimum": 0,
            "title": "Axial Force N",
            "type": "number"
          },
          "bending_moment_Nmm": {
            "description": "Applied bending moment about the depth axis, N*mm",
            "maximum": 100000000,
            "minimum": 0,
            "title": "Bending Moment Nmm",
            "type": "number"
          },
          "tensile_strength_MPa": {
            "description": "Material tensile strength from the datasheet, MPa",
            "maximum": 200,
            "minimum": 1,
            "title": "Tensile Strength Mpa",
            "type": "number"
          },
          "interlayer_strength_factor": {
            "description": "Z-direction strength as a fraction of tensile strength, 0.05-1",
            "maximum": 1,
            "minimum": 0.05,
            "title": "Interlayer Strength Factor",
            "type": "number"
          },
          "required_safety_factor": {
            "default": 2,
            "description": "Minimum acceptable safety factor",
            "maximum": 20,
            "minimum": 1,
            "title": "Required Safety Factor",
            "type": "number"
          }
        },
        "required": [
          "section_width_mm",
          "section_depth_mm",
          "shift_mm",
          "axial_force_N",
          "bending_moment_Nmm",
          "tensile_strength_MPa",
          "interlayer_strength_factor"
        ],
        "title": "layer_shift_strength_checkArguments"
      },
      "outputSchema": {
        "type": "object",
        "properties": {
          "bonded_area_mm2": {
            "description": "Overlap area across the shifted interface, mm^2",
            "title": "Bonded Area Mm2",
            "type": "number"
          },
          "area_retained_fraction": {
            "title": "Area Retained Fraction",
            "type": "number"
          },
          "peak_stress_MPa": {
            "anyOf": [
              {
                "type": "number"
              },
              {
                "type": "null"
              }
            ],
            "description": "Axial + bending stress at the interface; null if separated",
            "title": "Peak Stress Mpa"
          },
          "allowable_stress_MPa": {
            "description": "tensile_strength x interlayer_strength_factor, MPa",
            "title": "Allowable Stress Mpa",
            "type": "number"
          },
          "safety_factor": {
            "title": "Safety Factor",
            "type": "number"
          },
          "intact_safety_factor": {
            "description": "Safety factor of the same section with no shift",
            "title": "Intact Safety Factor",
            "type": "number"
          },
          "strength_retained_fraction": {
            "description": "Intact peak stress / shifted peak stress",
            "title": "Strength Retained Fraction",
            "type": "number"
          },
          "meets_requirement": {
            "description": "safety_factor >= required_safety_factor",
            "title": "Meets Requirement",
            "type": "boolean"
          },
          "note": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Note"
          }
        },
        "required": [
          "bonded_area_mm2",
          "area_retained_fraction",
          "peak_stress_MPa",
          "allowable_stress_MPa",
          "safety_factor",
          "intact_safety_factor",
          "strength_retained_fraction",
          "meets_requirement",
          "note"
        ],
        "title": "StrengthResult"
      },
      "annotations": {
        "readOnlyHint": true,
        "destructiveHint": false,
        "idempotentHint": true,
        "openWorldHint": false
      }
    }
  ]
}
```

## 2. Original tool (HW4 Tool 2): check_recovery_feasibility

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name check_recovery_feasibility --tool-arg correction_mm=2 --tool-arg max_correction_per_layer_mm=0.25 --tool-arg remaining_layers=15 --tool-arg layer_height_mm=0.2
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"required_layers\": 8,\n  \"transition_height_mm\": 1.6,\n  \"spare_layers\": 7,\n  \"feasible\": true\n}"
    }
  ],
  "structuredContent": {
    "required_layers": 8,
    "transition_height_mm": 1.6,
    "spare_layers": 7,
    "feasible": true
  },
  "isError": false
}
```

## 3. Original tool (HW4 Tool 3): expected_recovery_savings

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name expected_recovery_savings --tool-arg restart_time_h=5 --tool-arg recovery_time_h=2 --tool-arg intervention_time_h=0.25 --tool-arg restart_filament_g=120 --tool-arg recovery_filament_g=50 --tool-arg success_probability=0.8
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"expected_recovery_time_h\": 3.25,\n  \"expected_time_savings_h\": 1.75,\n  \"expected_recovery_filament_g\": 74.0,\n  \"expected_filament_savings_g\": 46.0,\n  \"breakeven_probability_time\": 0.45\n}"
    }
  ],
  "structuredContent": {
    "expected_recovery_time_h": 3.25,
    "expected_time_savings_h": 1.75,
    "expected_recovery_filament_g": 74,
    "expected_filament_savings_g": 46,
    "breakeven_probability_time": 0.45
  },
  "isError": false
}
```

## 4. New tool: early_stop_trend_alarm (warp lift growing over the first 50 of 200 layers)

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name early_stop_trend_alarm --tool-arg layer_numbers=[10,20,30,40,50] --tool-arg deviations_mm=[0.05,0.10,0.16,0.21,0.25] --tool-arg tolerance_mm=0.5 --tool-arg total_layers=200 --tool-arg total_print_time_h=8 --tool-arg total_filament_g=150
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"alert_level\": \"STOP\",\n  \"trend_slope_mm_per_layer\": 0.0051,\n  \"trend_r_squared\": 0.996,\n  \"current_layer\": 50,\n  \"current_deviation_mm\": 0.25,\n  \"projected_final_deviation_mm\": 1.021,\n  \"projected_exceedance_layer\": 98,\n  \"layers_until_exceedance\": 48,\n  \"remaining_fraction_of_print\": 0.75,\n  \"time_saved_if_stopped_now_h\": 6.0,\n  \"filament_saved_if_stopped_now_g\": 112.5\n}"
    }
  ],
  "structuredContent": {
    "alert_level": "STOP",
    "trend_slope_mm_per_layer": 0.0051,
    "trend_r_squared": 0.996,
    "current_layer": 50,
    "current_deviation_mm": 0.25,
    "projected_final_deviation_mm": 1.021,
    "projected_exceedance_layer": 98,
    "layers_until_exceedance": 48,
    "remaining_fraction_of_print": 0.75,
    "time_saved_if_stopped_now_h": 6,
    "filament_saved_if_stopped_now_g": 112.5
  },
  "isError": false
}
```

## 5. New tool: layer_shift_strength_check (4 mm shift on a 20 x 10 mm section, 500 N in Z)

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name layer_shift_strength_check --tool-arg section_width_mm=20 --tool-arg section_depth_mm=10 --tool-arg shift_mm=4 --tool-arg axial_force_N=500 --tool-arg bending_moment_Nmm=0 --tool-arg tensile_strength_MPa=50 --tool-arg interlayer_strength_factor=0.5
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "{\n  \"bonded_area_mm2\": 160.0,\n  \"area_retained_fraction\": 0.8,\n  \"peak_stress_MPa\": 5.469,\n  \"allowable_stress_MPa\": 25.0,\n  \"safety_factor\": 4.571,\n  \"intact_safety_factor\": 10.0,\n  \"strength_retained_fraction\": 0.4571,\n  \"meets_requirement\": true,\n  \"note\": null\n}"
    }
  ],
  "structuredContent": {
    "bonded_area_mm2": 160,
    "area_retained_fraction": 0.8,
    "peak_stress_MPa": 5.469,
    "allowable_stress_MPa": 25,
    "safety_factor": 4.571,
    "intact_safety_factor": 10,
    "strength_retained_fraction": 0.4571,
    "meets_requirement": true,
    "note": null
  },
  "isError": false
}
```

## 6. Invalid input (schema range): success probability given as 80 instead of 0.8

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name expected_recovery_savings --tool-arg restart_time_h=5 --tool-arg recovery_time_h=2 --tool-arg intervention_time_h=0.25 --tool-arg restart_filament_g=120 --tool-arg recovery_filament_g=50 --tool-arg success_probability=80
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error executing tool expected_recovery_savings: 1 validation error for expected_recovery_savingsArguments\nsuccess_probability\n  Input should be less than or equal to 1 [type=less_than_equal, input_value=80, input_type=int]\n    For further information visit https://errors.pydantic.dev/2.14/v/less_than_equal"
    }
  ],
  "isError": true
}
```

Server / Inspector log (stderr):

```text
[11/07/26 16:38:09] INFO     Tool 'expected_recovery_savings'      server.py:450
                             rejected arguments:                                
                             ['success_probability']                            
{"error":{"code":"tool_is_error","message":"Tool 'expected_recovery_savings' returned isError:true."}}
```

## 7. Invalid input (domain rule): wall thicker than the radius

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name check_functional_geometry --tool-arg outer_radius_mm=20 --tool-arg wall_thickness_mm=25 --tool-arg height_mm=50 --tool-arg base_thickness_mm=2 --tool-arg min_capacity_mL=45
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error executing tool check_functional_geometry: Invalid input: wall thickness must be < outer radius and base thickness must be < height"
    }
  ],
  "isError": true
}
```

Server / Inspector log (stderr):

```text
[11/07/26 16:38:10] INFO     Tool 'check_functional_geometry'      server.py:453
                             failed: 'Error executing tool                      
                             check_functional_geometry: Invalid                 
                             input: wall thickness must be < outer              
                             radius and base thickness must be <                
                             height'                                            
{"error":{"code":"tool_is_error","message":"Tool 'check_functional_geometry' returned isError:true."}}
```

## 8. Invalid input (new tool): layer and deviation lists of different lengths

```bash
npx @modelcontextprotocol/inspector --cli python server.py --method tools/call --tool-name early_stop_trend_alarm --tool-arg layer_numbers=[10,20,30,40] --tool-arg deviations_mm=[0.05,0.10,0.16] --tool-arg tolerance_mm=0.5 --tool-arg total_layers=200
```

```json
{
  "content": [
    {
      "type": "text",
      "text": "Error executing tool early_stop_trend_alarm: Invalid input: layer_numbers (4) and deviations_mm (3) must have the same length"
    }
  ],
  "isError": true
}
```

Server / Inspector log (stderr):

```text
[11/07/26 16:38:11] INFO     Tool 'early_stop_trend_alarm' failed: server.py:453
                             'Error executing tool                              
                             early_stop_trend_alarm: Invalid                    
                             input: layer_numbers (4) and                       
                             deviations_mm (3) must have the same               
                             length'                                            
{"error":{"code":"tool_is_error","message":"Tool 'early_stop_trend_alarm' returned isError:true."}}
```

