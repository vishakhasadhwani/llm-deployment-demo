# AWS EC2 g4dn.xlarge — Setup Guide

Complete steps to provision and configure a GPU instance for running vLLM Nexus.

---

## Instance Specs

| Property | Value |
|---|---|
| Instance type | g4dn.xlarge |
| GPU | NVIDIA Tesla T4 (16 GB VRAM) |
| vCPUs | 4 |
| RAM | 16 GB |
| Storage | 100 GB EBS (gp3 recommended) |
| OS | Ubuntu 22.04 LTS |
| Estimated cost | ~$0.52/hr on-demand |

**Security Group — open these ports:**

| Port | Purpose |
|---|---|
| 22 | SSH |
| 80 | Streamlit UI |
| 8000 | vLLM API |

---

## Step 1 — SSH into the Instance

```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>
```

---

## Step 2 — Verify GPU Driver

```bash
nvidia-smi
```

You should see the Tesla T4 with CUDA 12.2+. If not, install the driver:

```bash
sudo apt install -y nvidia-driver-535
sudo reboot
```

After reboot, SSH back in and run `nvidia-smi` again to confirm.

---

## Step 3 — Install Docker

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

If Docker fails to start:

```bash
sudo systemctl reset-failed docker
sudo systemctl start docker
sudo systemctl status docker
```

---

## Step 4 — Install NVIDIA Container Toolkit

Allows Docker containers to access the GPU.

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

Test GPU access from inside Docker:

```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-base-ubuntu22.04 nvidia-smi
```

The T4 should appear inside the container output.

---

## Step 5 — Copy Project Files

```bash
mkdir -p ~/vllm-chat-app
cd ~/vllm-chat-app
```

Copy these files into the directory:
- `app.py`
- `Dockerfile`
- `entrypoint.sh`
- `requirements.txt`

Or clone directly from GitHub:

```bash
git clone https://github.com/vishakhasadhwani/llm-deployment-demo.git
cd llm-deployment-demo
```

---

## Step 6 — Create .dockerignore

```bash
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
vllm-env
.cache
EOF
```

---

## Step 7 — Build the Docker Image

```bash
docker build -t vllm-nexus .
```

> First build takes 10–20 minutes (downloads PyTorch ~800 MB + vLLM ~200 MB). Subsequent builds use layer cache.

---

## Step 8 — Run the Container

```bash
docker run --gpus all \
    -p 80:80 \
    -p 8000:8000 \
    -e MODEL_ID=Qwen/Qwen2-1.5B-Instruct \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    vllm-nexus
```

**Run in background (detached):**

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

Stop and remove:

```bash
docker stop vllm-nexus
docker rm vllm-nexus
```

---

## Step 9 — Access the UI

Open your browser and go to:

```
http://<your-ec2-public-ip>
```

The UI shows **SERVER OFFLINE** for the first 1–3 minutes while the model loads. Click **REFRESH** in the sidebar once ready.

---

## Disk Space Management

Models and Docker images consume significant disk. Clean up when needed:

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

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MODEL_ID` | `Qwen/Qwen2-1.5B-Instruct` | HuggingFace model ID |
| `GPU_UTIL` | `0.85` | Fraction of GPU VRAM to use |
| `MAX_MODEL_LEN` | `2048` | Max context length in tokens |
| `VLLM_HOST` | `http://localhost:8000` | vLLM server URL (used by Streamlit) |

---

## Supported Models (Tesla T4 — 16 GB VRAM)

| Model | HuggingFace ID | VRAM | Quality |
|---|---|---|---|
| Qwen2 1.5B Instruct | `Qwen/Qwen2-1.5B-Instruct` | ~3 GB | Good |
| TinyLlama 1.1B Chat | `TinyLlama/TinyLlama-1.1B-Chat-v1.0` | ~2 GB | Basic |
| Gemma 2B Instruct | `google/gemma-2b-it` | ~5 GB | Good |
| Phi-3 Mini Instruct | `microsoft/Phi-3-mini-4k-instruct` | ~8 GB | Very good |

Switch models by changing `MODEL_ID`:

```bash
-e MODEL_ID=microsoft/Phi-3-mini-4k-instruct
```
