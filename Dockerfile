FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3-pip \
    python3-venv \
    gnupg2 \
    lsb-release \
    ca-certificates \
    apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

# Installation of Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Add Ollama PATH to use as a command
ENV PATH="/root/.ollama/bin:$PATH"

RUN pip3 install --no-cache-dir streamlit ollama

WORKDIR /app

COPY ./chatbot.py /app/chatbot.py

EXPOSE 8501

CMD ollama serve & sleep 5 && ollama run gemma2:2b && streamlit run chatbot.py --server.port=8501 --server.address=0.0.0.0