# ⚡ vLLM Nexus

A self-hosted LLM chat interface powered by [vLLM](https://github.com/vllm-project/vllm) and [Streamlit](https://streamlit.io), designed to run on an AWS EC2 GPU instance (Tesla T4 / g4dn.xlarge).

---

## Architecture

```
Browser → Port 80 (Streamlit UI) → Port 8000 (vLLM OpenAI-compatible API) → Tesla T4 GPU
```

Both the vLLM inference server and the Streamlit frontend run inside a single Docker container. The entrypoint script starts vLLM first, waits for it to be healthy, then launches Streamlit.

---

## Requirements

### Hardware
- AWS EC2 instance: **g4dn.xlarge** (or any instance with an NVIDIA Tesla T4)
- Storage: **100 GB** EBS volume (models can be 2–15 GB)
- Ports open in Security Group: **80** (HTTP) and **8000** (vLLM API)

### Software
- Ubuntu 22.04 / 24.04
- NVIDIA Driver **535+** (CUDA 12.2+)
- Docker
- NVIDIA Container Toolkit

---

## Project Structure

```
vllm-chat-app/
├── app.py              # Streamlit chat frontend
├── entrypoint.sh       # Container startup script
├── Dockerfile          # Docker image definition
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Installation & Setup

### Step 1 — Verify GPU Driver

SSH into your instance and confirm the GPU is visible:

```bash
nvidia-smi
```

You should see the Tesla T4 listed with CUDA Version 12.2+. If not, install the driver:

```bash
sudo apt install -y nvidia-driver-535
sudo reboot
```

---

### Step 2 — Install Docker

```bash
sudo dpkg --configure -a

sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

Verify Docker is running:

```bash
docker ps
```

---

### Step 3 — Install NVIDIA Container Toolkit

This allows Docker containers to access the GPU:

```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

Verify GPU is accessible from Docker:

```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

---

### Step 4 — Clone / Copy Project Files

Make sure all project files are in the same directory:

```bash
mkdir -p ~/vllm-chat-app
cd ~/vllm-chat-app

# Place these files here:
# app.py, Dockerfile, entrypoint.sh, requirements.txt
ls
```

---

### Step 5 — Create .dockerignore

Prevents large local folders from being sent to the Docker build context:

```bash
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
vllm-env
.cache
EOF
```

---

### Step 6 — Build the Docker Image

```bash
cd ~/vllm-chat-app
docker build -t vllm-nexus .
```

> This will take **10–20 minutes** on first build as it downloads PyTorch (~800 MB) and vLLM (~200 MB). Subsequent builds use the layer cache and are much faster.

---

## Running the Application

### Basic Run

```bash
docker run --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm-nexus
```

The `-v ~/.cache/huggingface` flag mounts your local model cache into the container so models are not re-downloaded on every restart.

### Run in Background (detached)

```bash
docker run -d --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    --name vllm-nexus \
    vllm-nexus
```

Check logs:

```bash
docker logs -f vllm-nexus
```

Stop the container:

```bash
docker stop vllm-nexus
docker rm vllm-nexus
```

---

## Accessing the UI

Once the container is running, open your browser and go to:

```
http://<your-ec2-public-ip>
```

The Streamlit UI will show **SERVER OFFLINE** for the first 1–3 minutes while the model loads. Once vLLM is ready it will switch to **SERVER ONLINE** automatically (hit the Refresh button in the sidebar).

---

## Supported Models

These models are confirmed to work on a Tesla T4 (16 GB VRAM) with this setup:

| Model | HuggingFace ID | VRAM | Quality |
|---|---|---|---|
| Qwen2 1.5B Instruct ✅ recommended | `Qwen/Qwen2-1.5B-Instruct` | ~3 GB | Good |
| TinyLlama 1.1B Chat | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ~2 GB | Basic |
| Gemma 2B Instruct | `google/gemma-2b-it` | ~5 GB | Good |
| Phi-3 Mini Instruct | `microsoft/Phi-3-mini-4k-instruct` | ~8 GB | Very good |

To switch models, change the `MODEL_ID` environment variable:

```bash
docker run --gpus all -p 80:80 -p 8000:8000 \
    -e MODEL_ID=TinyLlama/TinyLlama-1.1B-Chat-v1.0 \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm-nexus
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

## Disk Space Management

Models and Docker images consume significant disk. Use these commands to free space when needed:

```bash
# Check disk usage
df -h

# Check model cache size
du -sh ~/.cache/huggingface/hub/*

# Remove unused Docker images and containers
docker system prune -af

# Clear pip cache
pip cache purge
```

---

## Troubleshooting

**`could not select device driver "" with capabilities: [[gpu]]`**
NVIDIA Container Toolkit is not installed. Follow Step 3 above.

**`CUDA out of memory`**
The model is too large for available VRAM. Either reduce `MAX_MODEL_LEN` or switch to a smaller model.

**`ValueError: chat template not found`**
The model doesn't have a built-in chat template. Switch to a model with `instruct` or `chat` in its name.

**`ModuleNotFoundError: No module named 'pyairports'`**
Rebuild the Docker image — `pyairports` is in `requirements.txt` and will be included.

**UI shows SERVER OFFLINE after startup**
Wait 2–3 minutes for the model to fully load, then click **🔄 REFRESH** in the sidebar.

---

## Tech Stack

| Component | Technology |
|---|---|
| Inference Engine | vLLM 0.6.3 |
| Frontend | Streamlit 1.58 |
| Deep Learning | PyTorch 2.4.0 + CUDA 12.1 |
| Containerization | Docker + NVIDIA Container Toolkit |
| GPU | NVIDIA Tesla T4 (16 GB VRAM) |