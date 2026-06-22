FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_DISABLE_XET=1

RUN apt-get update && apt-get install -y \
    python3 python3-pip curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.4.0+cu121 torchvision==0.19.0+cu121 && \
    pip install -r requirements.txt

COPY app.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

EXPOSE 8000 80
ENTRYPOINT ["./entrypoint.sh"]