#!/bin/bash
#SBATCH --job-name=sglang_test
#SBATCH -p a6000
#SBATCH --qos=gpu_access
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:1
#SBATCH --mem=48G
#SBATCH --time=03:00:00
#SBATCH --output=logs/sglang_test_%j.out
#SBATCH --error=logs/sglang_test_%j.err

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
PHASE2_DIR="$HOME/work/llm_delib/phase2"
MODEL_PATH="/home/adinara/.cache/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18"
PORT=30000
CONDA_ENV="llm_delib_sglang"
INCENTIVES="uniform"
NUM_RUNS=1

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
mkdir -p "$PHASE2_DIR/logs"
cd "$PHASE2_DIR"

SGLANG_LOG="$PHASE2_DIR/logs/sglang_${SLURM_JOB_ID}.log"
EXPERIMENT_LOG="$PHASE2_DIR/logs/experiment_${SLURM_JOB_ID}.log"

echo "=========================================="
echo "Job ID:     $SLURM_JOB_ID"
echo "Node:       $SLURMD_NODENAME"
echo "GPU:        $CUDA_VISIBLE_DEVICES"
echo "Start:      $(date)"
echo "SGLang log: $SGLANG_LOG"
echo "Exp log:    $EXPERIMENT_LOG"
echo "=========================================="

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ─────────────────────────────────────────────
# CLEANUP HANDLER
# ─────────────────────────────────────────────
cleanup() {
    echo ""
    echo "[$(date)] Shutting down SGLang server..."
    if [ -f "$PHASE2_DIR/sglang_${SLURM_JOB_ID}.pid" ]; then
        kill "$(cat "$PHASE2_DIR/sglang_${SLURM_JOB_ID}.pid")" 2>/dev/null
        rm -f "$PHASE2_DIR/sglang_${SLURM_JOB_ID}.pid"
    fi
    echo "[$(date)] Done."
}
trap cleanup EXIT INT TERM

# ─────────────────────────────────────────────
# START SGLANG SERVER
# ─────────────────────────────────────────────
echo "[$(date)] Starting SGLang server on port $PORT..."
echo "[$(date)] SGLang output → $SGLANG_LOG"

python -m sglang.launch_server \
    --model-path "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --dtype bfloat16 \
    --watchdog-timeout 600 \
    --skip-server-warmup \
    > "$SGLANG_LOG" 2>&1 &

echo $! > "$PHASE2_DIR/sglang_${SLURM_JOB_ID}.pid"
echo "SGLang PID: $(cat "$PHASE2_DIR/sglang_${SLURM_JOB_ID}.pid")"

MAX_WAIT=300
ELAPSED=0
# until curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; do
until curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/health" 2>/dev/null | grep -q "^200$"; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    echo "  ...waiting for SGLang (${ELAPSED}s)"
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: SGLang did not start within ${MAX_WAIT}s. Last log:"
        tail -30 "$SGLANG_LOG"
        exit 1
    fi
done
echo "[$(date)] SGLang server ready after ${ELAPSED}s."

# ─────────────────────────────────────────────
# RUN EXPERIMENT
# ─────────────────────────────────────────────
export SGLANG_API_BASE="http://localhost:$PORT"

echo "[$(date)] Starting Phase 2 experiment..."
echo "[$(date)] Experiment output → $EXPERIMENT_LOG"

python run.py \
    --preset sglang_qwen3_14b \
    --incentive $INCENTIVES \
    --num-runs "$NUM_RUNS" \
    --num-agents 3 \
    --max-concurrent 2 \
    > "$EXPERIMENT_LOG" 2>&1

STATUS=$?

echo "=========================================="
echo "Experiment exit status: $STATUS"
echo "End: $(date)"
echo "=========================================="

SGLANG_ERRORS=$(grep -i "error\|exception\|critical" "$SGLANG_LOG" 2>/dev/null | head -20)
if [ -n "$SGLANG_ERRORS" ]; then
    echo "--- SGLang warnings/errors (from $SGLANG_LOG) ---"
    echo "$SGLANG_ERRORS"
fi

echo "--- Experiment tail (from $EXPERIMENT_LOG) ---"
tail -30 "$EXPERIMENT_LOG"

exit $STATUS


# WORKING ON ONE GPU only
# ─────────────────────────────────────────────
# RUN EXPERIMENT
# ─────────────────────────────────────────────
# PHASE1_DIR="$HOME/work/llm_delib/phase1"
# export SGLANG_API_BASE="http://localhost:$PORT"

# echo "[$(date)] Starting Phase 1 experiment..."
# echo "[$(date)] Experiment output → $EXPERIMENT_LOG"

# cd "$PHASE1_DIR"
# python main.py > "$EXPERIMENT_LOG" 2>&1

# STATUS=$?