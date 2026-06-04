# Dockerfile do Backend (FastAPI) — Aula 6, Part 4
# Elementos-chave (item 7.1 do roteiro): imagem base, diretório de
# trabalho, instalação de dependências, exposição de porta e comando
# de inicialização.

FROM python:3.12-slim

WORKDIR /app

# Instala dependências primeiro (aproveita cache de camadas do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da aplicação
COPY app ./app

# Porta do FastAPI/Uvicorn
EXPOSE 8000

# Inicializa o servidor; 0.0.0.0 para ser acessível fora do container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
