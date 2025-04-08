FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    curl git build-essential \
    && rm -rf /var/lib/apt/lists/*

# FROM ubuntu:22.04

# RUN apt-get update && apt-get install -y \
#     curl \
#     git \
#     python3-pip \
#     python3-venv \
#     gnupg2 \
#     lsb-release \
#     ca-certificates \
#     apt-transport-https \
#     && rm -rf /var/lib/apt/lists/*

# Installation of Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Add Ollama PATH to use as a command
ENV PATH="/root/.ollama/bin:$PATH"

COPY ./requirements.txt /tmp/requirements.txt

RUN pip3 install --no-cache-dir -r /tmp/requirements.txt

WORKDIR /app

COPY ./app /app/

RUN rm -rf ~/.cache/huggingface/transformers && \
    rm -rf ~/.cache/sentence-transformers

EXPOSE 8501

CMD ollama serve & sleep 3 && streamlit run chatbot.py --server.port=8501 --server.address=0.0.0.0 --server.runOnSave=True