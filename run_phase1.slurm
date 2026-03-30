#!/bin/bash
#SBATCH --job-name=phase1_qwen3_14b_test
#SBATCH --output=/work/users/a/d/adinara/llm_delib/logs/phase1_%j.out
#SBATCH --error=/work/users/a/d/adinara/llm_delib/logs/phase1_%j.err
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --partition=a100-gpu
#SBATCH --gres=gpu:nvidia_a100-pcie-40gb:1
#SBATCH --time=01:00:00      
#SBATCH --qos=gpu_access


# ─────────────────────────────────────────────
# CONFIGURATION — edit these for your cluster
# ─────────────────────────────────────────────
CONDA_ENV="llm_delib"
MODEL_PATH="/work/users/a/d/adinara/models/Qwen3-14B"

SGLANG_PORT=30000
SGLANG_HOST="127.0.0.1"
PROJECT_DIR="/work/users/a/d/adinara/llm_delib/phase1"    # path to your phase1 directory

# ─────────────────────────────────────────────
# SETUP
# ─────────────────────────────────────────────
mkdir -p logs

echo "================================================"
echo "Job ID      : $SLURM_JOB_ID"
echo "Node        : $SLURMD_NODENAME"
echo "GPUs        : $CUDA_VISIBLE_DEVICES"
echo "Start time  : $(date)"
echo "Model       : $MODEL_PATH"
echo "Project dir : $PROJECT_DIR"
echo "================================================"

# Activate conda
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate "$CONDA_ENV"

# ─────────────────────────────────────────────
# LAUNCH SGLANG SERVER
# ─────────────────────────────────────────────
echo ""
echo "[1/3] Launching SGLang server..."

python -m sglang.launch_server \
    --model-path "$MODEL_PATH" \
    --host "$SGLANG_HOST" \
    --port "$SGLANG_PORT" \
    --dtype bfloat16 \
    &   # run in background

SGLANG_PID=$!
echo "SGLang PID: $SGLANG_PID"

# ─────────────────────────────────────────────
# WAIT FOR SERVER TO BE READY
# ─────────────────────────────────────────────
echo ""
echo "[2/3] Waiting for SGLang server to be ready..."

MAX_WAIT=300   # seconds
ELAPSED=0
INTERVAL=10

until curl -s "http://$SGLANG_HOST:$SGLANG_PORT/health" > /dev/null 2>&1; do
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: SGLang server did not start within ${MAX_WAIT}s. Exiting."
        kill "$SGLANG_PID" 2>/dev/null
        exit 1
    fi
    echo "  ...still waiting (${ELAPSED}s elapsed)"
    sleep "$INTERVAL"
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo "Server ready after ${ELAPSED}s."

# ─────────────────────────────────────────────
# RUN EXPERIMENT
# ─────────────────────────────────────────────
echo ""
echo "[3/3] Running Phase 1 experiment..."

export SGLANG_API_BASE="http://$SGLANG_HOST:$SGLANG_PORT"

cd "$PROJECT_DIR"
python main.py
PYTHON_EXIT=$?

# ─────────────────────────────────────────────
# CLEANUP
# ─────────────────────────────────────────────
echo ""
echo "Experiment finished with exit code: $PYTHON_EXIT"
echo "Shutting down SGLang server (PID $SGLANG_PID)..."
kill "$SGLANG_PID" 2>/dev/null
wait "$SGLANG_PID" 2>/dev/null

echo "Done. End time: $(date)"
exit $PYTHON_EXIT
