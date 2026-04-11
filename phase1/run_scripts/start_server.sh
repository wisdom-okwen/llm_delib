#!/bin/bash
# start_server.sh — launches SGLang server and waits until ready

GPU_ID=${1:-1}
MODEL_PATH=${2:-"Qwen/Qwen3-14B"}
PORT=${3:-30000}

MAX_WAIT=300
ELAPSED=0
INTERVAL=10

echo "Starting SGLang server on GPU $GPU_ID, port $PORT..."

CUDA_VISIBLE_DEVICES=$GPU_ID python -m sglang.launch_server \
    --model-path "$MODEL_PATH" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --dtype bfloat16 \
	--log-level error > logs/sglang.log 2>&1 &

echo $! > sglang.pid
echo "SGLang PID: $(cat sglang.pid)"

# Stream log until server is ready
until curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; do
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
    if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
        echo "ERROR: SGLang did not start within ${MAX_WAIT}s. Last log:"
        tail -20 sglang.log
        exit 1
    fi
    echo "  ...waiting (${ELAPSED}s)"
done

echo "SGLang server ready after ${ELAPSED}s."