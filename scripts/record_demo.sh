#!/usr/bin/env bash
# Record a chat demo against an Agent Bricks Workbench UI with agent-browser.
# Usage: record_demo.sh <session> <out.webm> <screenshot-prefix> "<question 1>" ["<question 2>" ...]
set -uo pipefail
SESSION="$1"; OUT="$2"; PREFIX="$3"; shift 3
ab() { agent-browser --session "$SESSION" "$@"; }
status() { ab eval "document.querySelector('[aria-label=\"Agent chat\"]')?.innerText.split('\n')[1] || ''" 2>/dev/null | tr -d '"\n'; }
ask() {
  ab find label "Message the agent" click >/dev/null 2>&1
  ab keyboard type "$1" >/dev/null 2>&1
  ab wait 700 >/dev/null; ab press Enter >/dev/null 2>&1
  local s=$(date +%s) st el
  while true; do
    sleep 3; st=$(status); el=$(( $(date +%s) - s ))
    [ $(( el % 15 )) -lt 3 ] && echo "  t=${el}s ${st}"
    if [ "$el" -gt 12 ] && [ "$st" = "Ready" ]; then echo "  done in ${el}s"; break; fi
    if [ "$el" -gt 300 ]; then echo "  TIMEOUT"; break; fi
  done
}
ab record start "$OUT" | tail -1
ab wait 1500 >/dev/null
i=0
for q in "$@"; do
  i=$((i+1)); echo "Q$i"; ask "$q"
  ab wait 2500 >/dev/null; ab screenshot "${PREFIX}-q${i}.png" >/dev/null 2>&1
done
ab record stop | tail -1
ab eval "(() => { const t=document.querySelector('[aria-label=\"Agent chat\"]').innerText; return JSON.stringify({tracebacks:(t.match(/Traceback/g)||[]).length, run_python_calls:(t.match(/run_python\(/g)||[]).length}); })()" | tail -1
