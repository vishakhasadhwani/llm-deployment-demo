# Local Qwen Deployment on vLLM

Run a private, self-hosted LLM chat interface on your own GPU — no API keys, no per-token costs, no data leaving your machine. This project deploys **Qwen2-1.5B-Instruct** (or any compatible HuggingFace model) using **vLLM** as the inference engine and **Streamlit** as the chat frontend, packaged in a single Docker container.

📊 **[Visual Walkthrough — Slides](./slides/vllm-deployment-docker.pdf)**

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

## Quick Start

### Step 1 — Launch a g4dn.xlarge Instance on AWS

Provision an EC2 GPU instance with the right AMI, security group, and storage. Full steps here:

**[g4-instance-setup.md](./g4-instance-setup.md)**

---

### Step 2 — SSH into the Instance

Once the instance is running, copy the Public IPv4 address from the AWS Console and connect:

```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>
```

---

### Step 3 — Clone the Repo

```bash
git clone https://github.com/vishakhasadhwani/llm-deployment-demo.git
cd llm-deployment-demo
```

---

### Step 4 — Build the Docker Image

```bash
docker build -t vllm-nexus .
```

> First build takes 10–20 minutes. Subsequent builds use the layer cache.

---

### Step 5 — Run the Container

```bash
docker run --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm-nexus
```

**Run in background:**

```bash
docker run -d --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --name vllm-nexus \
    vllm-nexus

docker logs -f vllm-nexus                        # watch logs
docker stop vllm-nexus && docker rm vllm-nexus   # stop and clean up
```

---

### Step 6 — Open the UI

```
http://<your-ec2-public-ip>
```

The UI shows **SERVER OFFLINE** for 1–3 minutes while the model loads — hit **REFRESH** in the sidebar once ready.

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
