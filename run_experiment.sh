#!/bin/bash
# run_experiment.sh — runs Phase 1 experiment against a running SGLang server

PORT=${1:-30000}
PROJECT_DIR=${2:-"$(dirname "$0")/phase1"}

export SGLANG_API_BASE="http://localhost:$PORT"

echo "Running experiment against $SGLANG_API_BASE"
echo "Project dir: $PROJECT_DIR"

cd "$PROJECT_DIR"
python main.py