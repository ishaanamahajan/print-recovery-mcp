# 3D Print Recovery Assistant: MCP Server

CMU 24-679 (Automated Science), Homework 5, Question 4.

This is a local [Model Context Protocol](https://modelcontextprotocol.io) server. It exposes five read-only tools for deciding what to do about a failing or failed FDM 3D print. Tools 1–3 come unchanged from Homework 4. Tools 4–5 are new.

| # | Tool | Question it answers | Origin |
|---|---|---|---|
| 1 | `check_functional_geometry` | Does the container still hold the required volume? | HW4 |
| 2 | `check_recovery_feasibility` | Can the remaining layers absorb the contour correction? | HW4 |
| 3 | `expected_recovery_savings` | Does trying to recover save time and filament on average? | HW4 |
| 4 | `early_stop_trend_alarm` | While printing: should I stop now (OK / WATCH / STOP), and what would stopping save? | **new** |
| 5 | `layer_shift_strength_check` | After a layer shift: does the part still carry its load? | **new** |

The server runs locally over stdio and makes no network calls. It never sends commands to a printer.

## Setup

You need Python 3.10 or later. Node 22 or later is only needed for MCP Inspector.

```bash
git clone https://github.com/ishaanamahajan/print-recovery-mcp.git
cd print-recovery-mcp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest -q          # 20 tests, including hand-calculation checks
```

## Connect a client

**MCP Inspector (GUI)**

```bash
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```

**MCP Inspector (CLI, reproduces the demo)**

```bash
bash demo/run_inspector_demo.sh        # writes demo/inspector_transcript.md
```

**Claude Code**

```bash
claude mcp add print-recovery -- "$PWD/.venv/bin/python" "$PWD/server.py"
```

**Claude Desktop.** Add this to `claude_desktop_config.json`, using absolute paths:

```json
{ "mcpServers": { "print-recovery": {
    "command": "/ABS/PATH/print-recovery-mcp/.venv/bin/python",
    "args": ["/ABS/PATH/print-recovery-mcp/server.py"] } } }
```

> **Apple Silicon with an x86_64 (Rosetta) Node.** Clients built on Node launch Python under the same architecture as Node. The arm64 `pydantic_core` then fails to load and the client reports "Connection closed". To fix it, launch with `arch -arm64 /path/.venv/bin/python server.py` (the demo script does this automatically) or install an arm64 Node.

## Tool contracts

All five tools follow the same rules.

- **Inputs.** Each tool has a JSON Schema in which every number carries a `minimum` and `maximum` and a unit in both its name and its description. The client sees these ranges before it calls.
- **Results.** Each tool has an `outputSchema`. A call returns `structuredContent` (typed JSON) plus the same JSON as text.
- **Annotations.** Every tool is marked `readOnlyHint: true`, `destructiveHint: false`, `idempotentHint: true` and `openWorldHint: false`.
- **Invalid inputs.** No partial result is ever returned. The server rejects bad input in one of two layers, and both return `isError: true` with a message naming the field:
  1. **Schema layer (pydantic).** Wrong types, out-of-range values and lists that are too short are rejected before the tool runs. Example: `success_probability = 80` gives "Input should be less than or equal to 1".
  2. **Domain layer (the tool's own checks).** These catch rules that involve more than one input, such as wall thickness ≥ radius, mismatched list lengths, layers not increasing, the last measured layer past the end of the print, or no load given. They are raised as `ToolError("Invalid input: …")`.

### 1. `check_functional_geometry` (HW4)

$V = \pi (r-t)^2 (H-b) / 1000$ mL

| Input | Unit | Range |
|---|---|---|
| `outer_radius_mm` | mm | 1–500 |
| `wall_thickness_mm` | mm | 0.4–50, < radius |
| `height_mm` | mm | 1–1000 |
| `base_thickness_mm` | mm | 0.2–100, < height |
| `min_capacity_mL` | mL | 0–10⁶ |

- **Result:** `estimated_capacity_mL`, `margin_mL`, `meets_requirement`.
- **Limitation:** assumes an ideal cylinder filled to the brim. Capacity does not prove the container is watertight.

### 2. `check_recovery_feasibility` (HW4)

$N_{req} = \lceil c/\Delta_{max} \rceil$, and recovery is feasible if $N_{req} \le N_{rem}$.

| Input | Unit | Range |
|---|---|---|
| `correction_mm` | mm | 0–50 |
| `max_correction_per_layer_mm` | mm/layer | 0.01–2 |
| `remaining_layers` | layers | integer, 0–100,000 |
| `layer_height_mm` | mm | 0.04–1.0 |

- **Result:** `required_layers`, `transition_height_mm`, `spare_layers`, `feasible`.
- **Limitation:** $\Delta_{max}$ is an assumed value, not a measured capability of the printer.

### 3. `expected_recovery_savings` (HW4)

$E[T] = T_{int} + T_{rec} + (1-p)T_{restart}$ and $E[F] = F_{rec} + (1-p)F_{restart}$.

| Input | Unit | Range |
|---|---|---|
| `restart_time_h` | h | 0.01–1000 |
| `recovery_time_h` | h | 0–1000 |
| `intervention_time_h` | h | 0–100 |
| `restart_filament_g` | g | 0.1–10⁵ |
| `recovery_filament_g` | g | 0–10⁵ |
| `success_probability` | fraction | 0–1 |

- **Result:** `expected_recovery_time_h`, `expected_time_savings_h`, `expected_recovery_filament_g`, `expected_filament_savings_g`, `breakeven_probability_time`.
- **Limitation:** risk-neutral and assumes a single recovery attempt. The user supplies $p$.

### 4. `early_stop_trend_alarm` (new)

The tool fits a least-squares line $d(n) = a + bn$ to deviations measured during the print, such as warp lift, layer-shift offset or under-extrusion width, and extrapolates it to the final layer.

| Alert | Condition |
|---|---|
| **STOP** | Latest deviation ≥ tolerance, or the projected final deviation ≥ tolerance |
| **WATCH** | Either value ≥ `watch_fraction` × tolerance |
| **OK** | Otherwise |

| Input | Unit | Range |
|---|---|---|
| `layer_numbers` | layers | list of 3–10,000 integers, strictly increasing, 0–100,000 |
| `deviations_mm` | mm | list of the same length, each 0–50 |
| `tolerance_mm` | mm | 0.01–50 |
| `total_layers` | layers | integer 1–100,000, ≥ last measured layer |
| `watch_fraction` | fraction | 0.1–0.99 (default 0.5) |
| `total_print_time_h` | h | 0.01–1000 (optional) |
| `total_filament_g` | g | 0.1–10⁵ (optional) |

**Result:**
- `alert_level`
- `trend_slope_mm_per_layer`, `trend_r_squared`
- `current_layer`, `current_deviation_mm`
- `projected_final_deviation_mm`, `projected_exceedance_layer`, `layers_until_exceedance` (the last two are `null` if the trend never reaches the tolerance)
- `remaining_fraction_of_print`
- `time_saved_if_stopped_now_h`, `filament_saved_if_stopped_now_g` (`null` if the optional inputs are omitted)

**Limitations:**
- The trend is a straight-line extrapolation, so a low `trend_r_squared` means the projection is unreliable.
- Savings assume time and filament are spread evenly across layers.
- The deviations come from whatever is measuring the print (a camera or the user), and the tool does not check them.

### 5. `layer_shift_strength_check` (new)

A shift $s$ along the section width $W$ leaves a bonded overlap of $(W-s) \times D$. The load still acts through the centre of the upper part, so the shift adds an eccentric moment $Fs/2$.

$\sigma_{peak} = \dfrac{F}{A} + \dfrac{(M + Fs/2)\,c}{I}$, with $A = (W-s)D$, $I = D(W-s)^3/12$ and $c = (W-s)/2$.

Allowable stress = `tensile_strength_MPa` × `interlayer_strength_factor`. The result is compared against the same section with no shift.

| Input | Unit | Range |
|---|---|---|
| `section_width_mm` (along the shift) | mm | 1–500 |
| `section_depth_mm` | mm | 1–500 |
| `shift_mm` | mm | 0–500 |
| `axial_force_N` (tension across layers) | N | 0–10⁵ |
| `bending_moment_Nmm` | N·mm | 0–10⁸ |
| `tensile_strength_MPa` (datasheet) | MPa | 1–200 |
| `interlayer_strength_factor` | fraction | 0.05–1 |
| `required_safety_factor` | – | 1–20 (default 2) |

At least one of the force and the moment must be positive. A shift of at least the full width returns `safety_factor: 0` with a "separated" note rather than an error.

- **Result:** `bonded_area_mm2`, `area_retained_fraction`, `peak_stress_MPa`, `allowable_stress_MPa`, `safety_factor`, `intact_safety_factor`, `strength_retained_fraction`, `meets_requirement`, `note`.
- **Limitations:**
  - Uses beam theory on a solid rectangle. It ignores infill and perimeters, stress concentration at the step, and fatigue.
  - The interlayer factor is a user assumption and should be measured.

## Demo record

- [`demo/inspector_transcript.md`](demo/inspector_transcript.md): MCP Inspector (CLI mode) calls with full responses:
  - the tool list with schemas;
  - two HW4 tools;
  - both new tools;
  - three invalid inputs, covering a schema range, a domain rule and a new tool.
- [`demo/claude_code_transcript.md`](demo/claude_code_transcript.md): Claude Code calling the tools from plain-language questions, including a unit conversion (480 min → 8 h).

## Client / server boundary

**Server (this repo):**
- the equations;
- unit and range validation, and the input schemas that publish it;
- typed structured results;
- error messages.

It is deterministic and stateless, makes no network calls, and cannot send commands to a printer.

**Client (Claude Code, Claude Desktop, Inspector):**
- understanding the request;
- converting units (minutes → hours, percent → fraction, diameter → radius);
- choosing the tool;
- asking for missing inputs instead of inventing them;
- explaining the result.

**Human:** makes the decision. The server can report STOP, but it never stops a print.

## Link to user research (HW5 requirements)

| Requirement | Interview evidence | Tool |
|---|---|---|
| R1: Detect failures early | Unattended overnight prints; adhesion and warping failures that spaghetti detection misses; wanting to pause prints in advance | `early_stop_trend_alarm` |
| R2: Judge function, not appearance | Visually imperfect parts are acceptable if they work; a part that looks fine may still be structurally weak | `layer_shift_strength_check`, `check_functional_geometry` |
| R3: Evidence and approval before changes | Distrust of automatic correction | All tools are read-only and return intermediate values |
| R5: Run offline | Concern about proprietary designs in the cloud | Local stdio server, no network |

## What a human should verify before acting

- **All tools:** check that the arguments the client sent match the real part and printer. Units are the most likely source of error.
- **`early_stop_trend_alarm`:**
  - look at the print before cancelling;
  - the trend is a straight-line extrapolation, and a low `trend_r_squared` means it is unreliable;
  - the input measurements are not verified by the tool.
- **`layer_shift_strength_check`:**
  - use measured strength values;
  - halving `interlayer_strength_factor` from 0.5 to 0.25 drops the demo safety factor from 4.57 to about 2.3;
  - the model ignores infill, stress concentration at the step and fatigue;
  - for load-critical parts, pull-test a coupon with the same shift.
- **`check_recovery_feasibility` / `expected_recovery_savings`:** the per-layer correction limit and the success probability are assumptions that should be measured.

## Repository layout

```
tools.py       pure-Python tool functions (HW4 tools verbatim + 2 new); no MCP dependency
server.py      MCP server: schemas, result models, annotations, error mapping
tests/         pytest: hand-checked values, edge cases, invalid inputs, in-process MCP calls
demo/          Inspector CLI script + transcript, Claude Code transcript
LICENSE        MIT
```

## AI usage

Claude Code (Claude Opus 5.5) helped implement and test this server. The tool equations, ranges and design decisions were reviewed by the author.
