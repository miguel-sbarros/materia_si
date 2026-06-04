# Dockerfile do Frontend (Streamlit) — Aula 6, Part 5
# Imagem base Python, instalação de dependências, exposição da porta
# do Streamlit (8501) e comando de inicialização.

FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Porta padrão do Streamlit
EXPOSE 8501

# --server.address=0.0.0.0 expõe o app fora do container
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
