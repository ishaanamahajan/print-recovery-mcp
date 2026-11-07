#!/usr/bin/env bash
# Records the HW5 demo calls through the official MCP Inspector (CLI mode, stdio transport).
# Usage:  bash demo/run_inspector_demo.sh   (from the repo root, after setup in README)
# Writes: demo/inspector_transcript.md
set -u
cd "$(dirname "$0")/.."
PY="$PWD/.venv/bin/python"
# On Apple Silicon with an x86_64 (Rosetta) Node, force the Python child to arm64.
LAUNCH=("$PY" server.py)
if [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" || "$(sysctl -n sysctl.proc_translated 2>/dev/null)" == "1" ]]; then
  LAUNCH=(arch -arm64 "$PY" server.py)
fi
INSPECT=(npx -y @modelcontextprotocol/inspector@latest --cli "${LAUNCH[@]}")
OUT=demo/inspector_transcript.md

run() {  # run <title> <args...>
  local title="$1"; shift
  {
    echo "## $title"
    echo
    echo '```bash'
    echo "npx @modelcontextprotocol/inspector --cli python server.py $*"
    echo '```'
    echo
    local err; err=$(mktemp)
    echo '```json'
    "${INSPECT[@]}" "$@" 2>"$err"
    echo '```'
    if grep -q -v -e 'npm warn' -e 'npm WARN' "$err"; then
      echo
      echo "Server / Inspector log (stderr):"
      echo
      echo '```text'
      grep -v -e 'npm warn' -e 'npm WARN' "$err"
      echo '```'
    fi
    rm -f "$err"
    echo
  } >> "$OUT"
}

{
  echo "# MCP Inspector demo transcript"
  echo
  echo "Recorded $(date '+%Y-%m-%d %H:%M %Z') with \`@modelcontextprotocol/inspector\` (CLI mode) over stdio."
  echo "Server: \`print-recovery\` v1.0.0, MCP Python SDK $("$PY" -c 'import importlib.metadata as m; print(m.version("mcp"))')."
  echo
} > "$OUT"

run "1. List tools (full input and output schemas)" --method tools/list

run "2. Original tool (HW4 Tool 2): check_recovery_feasibility" \
  --method tools/call --tool-name check_recovery_feasibility \
  --tool-arg correction_mm=2 --tool-arg max_correction_per_layer_mm=0.25 \
  --tool-arg remaining_layers=15 --tool-arg layer_height_mm=0.2

run "3. Original tool (HW4 Tool 3): expected_recovery_savings" \
  --method tools/call --tool-name expected_recovery_savings \
  --tool-arg restart_time_h=5 --tool-arg recovery_time_h=2 --tool-arg intervention_time_h=0.25 \
  --tool-arg restart_filament_g=120 --tool-arg recovery_filament_g=50 --tool-arg success_probability=0.8

run "4. New tool: early_stop_trend_alarm (warp lift growing over the first 50 of 200 layers)" \
  --method tools/call --tool-name early_stop_trend_alarm \
  --tool-arg 'layer_numbers=[10,20,30,40,50]' --tool-arg 'deviations_mm=[0.05,0.10,0.16,0.21,0.25]' \
  --tool-arg tolerance_mm=0.5 --tool-arg total_layers=200 \
  --tool-arg total_print_time_h=8 --tool-arg total_filament_g=150

run "5. New tool: layer_shift_strength_check (4 mm shift on a 20 x 10 mm section, 500 N in Z)" \
  --method tools/call --tool-name layer_shift_strength_check \
  --tool-arg section_width_mm=20 --tool-arg section_depth_mm=10 --tool-arg shift_mm=4 \
  --tool-arg axial_force_N=500 --tool-arg bending_moment_Nmm=0 \
  --tool-arg tensile_strength_MPa=50 --tool-arg interlayer_strength_factor=0.5

run "6. Invalid input (schema range): success probability given as 80 instead of 0.8" \
  --method tools/call --tool-name expected_recovery_savings \
  --tool-arg restart_time_h=5 --tool-arg recovery_time_h=2 --tool-arg intervention_time_h=0.25 \
  --tool-arg restart_filament_g=120 --tool-arg recovery_filament_g=50 --tool-arg success_probability=80

run "7. Invalid input (domain rule): wall thicker than the radius" \
  --method tools/call --tool-name check_functional_geometry \
  --tool-arg outer_radius_mm=20 --tool-arg wall_thickness_mm=25 --tool-arg height_mm=50 \
  --tool-arg base_thickness_mm=2 --tool-arg min_capacity_mL=45

run "8. Invalid input (new tool): layer and deviation lists of different lengths" \
  --method tools/call --tool-name early_stop_trend_alarm \
  --tool-arg 'layer_numbers=[10,20,30,40]' --tool-arg 'deviations_mm=[0.05,0.10,0.16]' \
  --tool-arg tolerance_mm=0.5 --tool-arg total_layers=200

echo "Wrote $OUT"
