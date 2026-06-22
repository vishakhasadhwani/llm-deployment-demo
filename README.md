# Local Qwen Deployment on vLLM

Run a private, self-hosted LLM chat interface on your own GPU — no API keys, no per-token costs, no data leaving your machine. This project deploys **Qwen2-1.5B-Instruct** (or any compatible HuggingFace model) using **vLLM** as the inference engine and **Streamlit** as the chat frontend, packaged in a single Docker container.

---

## Self-Hosted Model vs API-Deployed Model

| | Self-Hosted (this project) | API-Based (OpenAI, Anthropic) |
|---|---|---|
| Cost | One-time GPU cost | Per-token billing |
| Privacy | Data stays on your machine | Data sent to third party |
| Control | Full — model, params, context length | Limited to what the API exposes |
| Setup | Requires GPU + Docker | Just an API key |
| Best for | Private data, cost at scale, learning | Quick prototyping, production apps |

---

## Architecture

```
Browser
  └── Port 80  →  Streamlit UI (app.py)
                      └── Port 8000  →  vLLM OpenAI-compatible API
                                            └── NVIDIA GPU (Tesla T4 / local)
```

Both services run inside a **single Docker container**. The entrypoint script starts vLLM first, polls `/health` until the model is loaded, then launches Streamlit.

---

## Key Component Workflow

### 1. Model Download from HuggingFace

vLLM pulls the model weights directly from [HuggingFace Hub](https://huggingface.co) at container startup using the `MODEL_ID` environment variable. Models are cached at `~/.cache/huggingface` and mounted into the container so they are not re-downloaded on restart.

```bash
-e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
-v ~/.cache/huggingface:/root/.cache/huggingface \
```

### 2. HuggingFace Token (for gated models)

Public models like Qwen2 and TinyLlama do not require a token. For gated models (e.g., Llama 3, Gemma), set your HF token:

```bash
-e HUGGING_FACE_HUB_TOKEN=hf_your_token_here
```

Generate a token at **huggingface.co → Settings → Access Tokens** (read permission is sufficient).

### 3. Dockerfile — Build & Deployment

The Dockerfile starts from the official NVIDIA CUDA runtime image, installs PyTorch (CUDA 12.1 build), then vLLM, Streamlit, and the remaining dependencies.

```dockerfile
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04
# installs PyTorch (cu121) + vLLM + Streamlit
EXPOSE 8000 80
ENTRYPOINT ["./entrypoint.sh"]
```

Build the image:

```bash
docker build -t vllm-nexus .
```

> First build takes 10–20 minutes (PyTorch ~800 MB + vLLM ~200 MB). Subsequent builds use the layer cache.

### 4. Inference with Streamlit

`app.py` connects to vLLM's OpenAI-compatible REST API at `http://localhost:8000`. It:
- Polls `/health` to show server status in the sidebar
- Lists available models from `/v1/models`
- Streams responses from `/v1/chat/completions` token by token
- Tracks request count, total tokens, and latency per request

---

## Project Structure

```
llm-deployment-demo/
├── app.py                  # Streamlit chat frontend
├── entrypoint.sh           # Starts vLLM then Streamlit
├── Dockerfile              # CUDA + PyTorch + vLLM + Streamlit image
├── requirements.txt        # Python dependencies
├── g4-instance-setup.md    # AWS EC2 g4dn.xlarge provisioning guide
└── README.md
```

---

## Quick Start — Local Run

**Requirements:** Docker + NVIDIA Container Toolkit installed, CUDA-capable GPU.

```bash
# Build
docker build -t vllm-nexus .

# Run
docker run --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm-nexus
```

Open `http://localhost`. The UI shows **SERVER OFFLINE** for 1–3 minutes while the model loads — hit **REFRESH** in the sidebar once ready.

**Run detached:**

```bash
docker run -d --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --name vllm-nexus \
    vllm-nexus

docker logs -f vllm-nexus   # watch logs
docker stop vllm-nexus && docker rm vllm-nexus
```

---

## Cloud Deployment — AWS EC2

For running on a remote GPU instance (g4dn.xlarge / Tesla T4), see the full provisioning guide:

**[g4-instance-setup.md](./g4-instance-setup.md)**

---

## Supported Models

Confirmed to work on Tesla T4 (16 GB VRAM):

| Model | HuggingFace ID | VRAM | Quality |
|---|---|---|---|
| Qwen2 1.5B Instruct ✅ recommended | `Qwen/Qwen2-1.5B-Instruct` | ~3 GB | Good |
| TinyLlama 1.1B Chat | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ~2 GB | Basic |
| Gemma 2B Instruct | `google/gemma-2b-it` | ~5 GB | Good |
| Phi-3 Mini Instruct | `microsoft/Phi-3-mini-4k-instruct` | ~8 GB | Very good |

Switch models by changing `MODEL_ID`:

```bash
-e MODEL_ID=microsoft/Phi-3-mini-4k-instruct
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_ID` | `Qwen/Qwen2-1.5B-Instruct` | HuggingFace model ID to load |
| `GPU_UTIL` | `0.85` | Fraction of GPU VRAM to use (0.0–1.0) |
| `MAX_MODEL_LEN` | `2048` | Maximum context length in tokens |
| `VLLM_HOST` | `http://localhost:8000` | vLLM server URL (used by Streamlit) |

---

## Troubleshooting

**`could not select device driver "" with capabilities: [[gpu]]`**
NVIDIA Container Toolkit is not installed or Docker wasn't restarted after install.

**`CUDA out of memory`**
Model too large for available VRAM. Reduce `MAX_MODEL_LEN` or switch to a smaller model.

**`ValueError: chat template not found`**
Use a model with `instruct` or `chat` in the name.

**UI shows SERVER OFFLINE after startup**
Wait 2–3 minutes for the model to load, then click **REFRESH** in the sidebar.

---

## Tech Stack

| Component | Technology |
|---|---|
| Inference Engine | vLLM 0.6.3 |
| Frontend | Streamlit 1.58 |
| Deep Learning | PyTorch 2.4.0 + CUDA 12.1 |
| Containerization | Docker + NVIDIA Container Toolkit |
| GPU | NVIDIA Tesla T4 (16 GB VRAM) |
