#!/bin/bash
# run_phase1.sh — master script: starts server, runs experiment, cleans up
set -e

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
GPU_ID=1
MODEL_PATH="Qwen/Qwen3-14B"
PORT=30000
PROJECT_DIR="$(dirname "$0")/phase1"

SCRIPT_DIR="$(dirname "$0")"

# ─────────────────────────────────────────────
# CLEANUP HANDLER
# ─────────────────────────────────────────────
cleanup() {
    echo ""
    echo "Shutting down SGLang server..."
    if [ -f sglang.pid ]; then
        kill "$(cat sglang.pid)" 2>/dev/null
        rm -f sglang.pid
    fi
    # Print any errors from server log on exit
    if [ -f sglang.log ]; then
        ERRORS=$(grep -i "error\|exception" sglang.log)
        if [ -n "$ERRORS" ]; then
            echo "SGLang errors detected:"
            echo "$ERRORS"
        fi
    fi
}
trap cleanup EXIT INT TERM

# ─────────────────────────────────────────────
# START SERVER
# ─────────────────────────────────────────────
bash "$SCRIPT_DIR/start_server.sh" "$GPU_ID" "$MODEL_PATH" "$PORT"

# ─────────────────────────────────────────────
# RUN EXPERIMENT
# ─────────────────────────────────────────────
bash "$SCRIPT_DIR/run_experiment.sh" "$PORT" "$PROJECT_DIR"