# AWS EC2 g4dn.xlarge — Instance Setup Guide

Full steps to launch and configure a GPU instance on AWS for running this project. For local deployment or project overview, see [README.md](./README.md).

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

---

## Step 1 — Launch the EC2 Instance

1. Go to **AWS Console → EC2 → Launch Instance**
2. **Name:** `vllm-nexus` (or any name)
3. **AMI:** Ubuntu Server 22.04 LTS (64-bit x86)
4. **Instance type:** `g4dn.xlarge`
   - Use the search bar and filter by GPU instances if it doesn't appear in the default list
5. **Key pair:** Create a new key pair or select an existing one — you'll need this to SSH in
6. **Network settings → Security Group:** Add the following inbound rules:

   | Type | Port | Source |
   |---|---|---|
   | SSH | 22 | My IP |
   | Custom TCP | 80 | 0.0.0.0/0 |
   | Custom TCP | 8000 | 0.0.0.0/0 |

7. **Configure storage:** Set root volume to **100 GB gp3**
   - Models range from 2–15 GB and Docker images add up — 100 GB gives comfortable headroom
8. Click **Launch Instance**

Once the instance is running, copy the **Public IPv4 address** from the instance details page.

---

## Step 2 — SSH into the Instance

```bash
ssh -i your-key.pem ubuntu@<ec2-public-ip>
```

If you get a permissions error on the key file:

```bash
chmod 400 your-key.pem
```

---

## Step 3 — Verify GPU Driver

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

## Step 4 — Install Docker

```bash
sudo dpkg --configure -a
sudo apt install -y docker.io
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker $USER
newgrp docker
```

Verify:

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

## Step 5 — Install NVIDIA Container Toolkit

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

The T4 should appear in the container output.

---

## Step 6 — Clone the Repo

```bash
git clone https://github.com/vishakhasadhwani/llm-deployment-demo.git
cd llm-deployment-demo
```

---

## Step 7 — Create .dockerignore

```bash
cat > .dockerignore << 'EOF'
__pycache__
*.pyc
vllm-env
.cache
EOF
```

---

## Step 8 — Build the Docker Image

```bash
docker build -t vllm-nexus .
```

> First build takes 10–20 minutes (downloads PyTorch ~800 MB + vLLM ~200 MB). Subsequent builds use the layer cache.

---

## Step 9 — Run the Container

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
docker stop vllm-nexus && docker rm vllm-nexus
```

---

## Step 10 — Access the UI

Open your browser and go to:

```
http://<your-ec2-public-ip>
```

The UI shows **SERVER OFFLINE** for the first 1–3 minutes while the model loads. Click **REFRESH** in the sidebar once ready.

---

## Disk Space Management

```bash
df -h                                    # check disk usage
du -sh ~/.cache/huggingface/hub/*        # check model cache size
docker system prune -af                  # remove unused images and containers
pip cache purge                          # clear pip cache
```

---

## Stopping the Instance

When not in use, **stop** (not terminate) the instance from the AWS Console to avoid ongoing charges. Your EBS volume and cached models are preserved when stopped.
