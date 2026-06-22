#!/bin/bash
set -e

MODEL_ID="${MODEL_ID:-Qwen/Qwen2-1.5B-Instruct}"
GPU_UTIL="${GPU_UTIL:-0.85}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-2048}"

echo "==> Starting vLLM server with model: $MODEL_ID"

python3 -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_ID" \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization "$GPU_UTIL" \
    --dtype float16 \
    --trust-remote-code \
    --max-model-len "$MAX_MODEL_LEN" \
    --guided-decoding-backend lm-format-enforcer \
    --served-model-name "$MODEL_ID" &

echo "==> Waiting for vLLM to be ready..."
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    echo "    waiting..."
    sleep 5
done

echo "==> vLLM ready! Starting Streamlit..."
exec streamlit run app.py --server.port 80 --server.address 0.0.0.0 --server.headless true