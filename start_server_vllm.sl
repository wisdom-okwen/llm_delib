#!/bin/bash
#SBATCH --job-name=vllm_test
#SBATCH -p a6000
#SBATCH --qos=gpu_access
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --gres=gpu:2
#SBATCH --nodelist=gpu4
#SBATCH --time=0
#SBATCH --output=logs/vllm_test_%j.out
#SBATCH --error=logs/vllm_test_%j.err

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────
PHASE2_DIR="$HOME/work/llm_delib/phase2"
# MODEL_PATH="/playpen-shared/adinara/huggingface/hub/models--Qwen--Qwen3-14B/snapshots/40c069824f4251a91eefaf281ebe4c544efd3e18"
MODEL_PATH="/playpen-shared/adinara/huggingface/hub/models--Qwen--Qwen3-32B/snapshots/9216db5781bf21249d130ec9da846c4624c16137"

PORT=30000
CONDA_ENV="delib_vllm"
NUM_RUNS=5

# ── Experiment mode ────────────────────────────────────────────────────────────
# Options:
#   core  → uniform / contribution / contribution_oracle (3 conditions)
#   full  → all 11 conditions
# ──────────────────────────────────────────────────────────────────────────────
EXPERIMENT_MODE="full"   # change to "core" for the smaller sweep

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
mkdir -p "$PHASE2_DIR/logs"
cd "$PHASE2_DIR"

VLLM_LOG="$PHASE2_DIR/logs/vllm_${SLURM_JOB_ID}.log"
EXPERIMENT_LOG="$PHASE2_DIR/logs/experiment_${SLURM_JOB_ID}.log"

echo "=========================================="
echo "Job ID:     $SLURM_JOB_ID"
echo "Node:       $SLURMD_NODENAME"
echo "GPU:        $CUDA_VISIBLE_DEVICES"
echo "Start:      $(date)"
echo "vLLM log:   $VLLM_LOG"
echo "Exp log:    $EXPERIMENT_LOG"
echo "=========================================="

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ─────────────────────────────────────────────
# CLEANUP HANDLER
# ─────────────────────────────────────────────
cleanup() {
    echo ""
    echo "[$(date)] Shutting down vLLM server..."
    if [ -f "$PHASE2_DIR/vllm_${SLURM_JOB_ID}.pid" ]; then
        kill "$(cat "$PHASE2_DIR/vllm_${SLURM_JOB_ID}.pid")" 2>/dev/null
        rm -f "$PHASE2_DIR/vllm_${SLURM_JOB_ID}.pid"
    fi
    echo "[$(date)] Done."
}
trap cleanup EXIT INT TERM

# ─────────────────────────────────────────────
# START VLLM SERVER
# ─────────────────────────────────────────────
echo "[$(date)] Starting vLLM server on port $PORT..."
echo "[$(date)] vLLM output → $VLLM_LOG"

export NCCL_P2P_DISABLE=1 # disable NCCL P2P  and custom all-reduce to avoid potential issues in multi-GPU setup
export PYTHONUNBUFFERED=1 # ensure real-time logging from vLLM
python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --dtype bfloat16 \
    --gpu-memory-utilization 0.90 \
    --max-model-len 32768 \
    --served-model-name "qwen3-32b" \
	--tensor-parallel-size 2 \
	--disable-custom-all-reduce \
    > "$VLLM_LOG" 2>&1 &

echo $! > "$PHASE2_DIR/vllm_${SLURM_JOB_ID}.pid"
echo "vLLM PID: $(cat "$PHASE2_DIR/vllm_${SLURM_JOB_ID}.pid")"

MAX_WAIT=300
ELAPSED=0
until curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/health" 2>/dev/null | grep -q "^200$"; do
    sleep 10
    ELAPSED=$((ELAPSED + 10))
    echo "  ...waiting for vLLM (${ELAPSED}s)"
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: vLLM did not start within ${MAX_WAIT}s. Last log:"
        tail -30 "$VLLM_LOG"
        exit 1
    fi
done
echo "[$(date)] vLLM server ready after ${ELAPSED}s."

# ─────────────────────────────────────────────
# RUN EXPERIMENT
# ─────────────────────────────────────────────
export VLLM_API_BASE="http://localhost:$PORT"

echo "[$(date)] Starting Phase 2 experiment..."
echo "[$(date)] Experiment output → $EXPERIMENT_LOG"

CORE_CONDITIONS="uniform contribution contribution_oracle"
FULL_CONDITIONS="uniform contribution contribution_oracle \
    counterfactual_contribution hybrid stake bid_to_speak \
    forced_sharing free_debate no_comm"

if [ "$EXPERIMENT_MODE" = "core" ]; then
    CONDITIONS="$CORE_CONDITIONS"
    echo "[$(date)] Mode: CORE (3 conditions)"
else
    CONDITIONS="$FULL_CONDITIONS"
    echo "[$(date)] Mode: FULL SWEEP (11 conditions)"
fi

# shellcheck disable=SC2086
python run.py \
    --preset vllm \
    --incentive $CONDITIONS \
    --num-runs "$NUM_RUNS" \
    --num-agents 10 \
    --max-concurrent 5 \
    > "$EXPERIMENT_LOG" 2>&1

STATUS=$?

echo "=========================================="
echo "Experiment exit status: $STATUS"
echo "End: $(date)"
echo "=========================================="

VLLM_ERRORS=$(grep -i "error\|exception\|critical" "$VLLM_LOG" 2>/dev/null | head -20)
if [ -n "$VLLM_ERRORS" ]; then
    echo "--- vLLM warnings/errors (from $VLLM_LOG) ---"
    echo "$VLLM_ERRORS"
fi

echo "--- Experiment tail (from $EXPERIMENT_LOG) ---"
tail -30 "$EXPERIMENT_LOG"

exit $STATUS