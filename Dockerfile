FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
ENV RPC_CONTRACTS_VERSION=0.1.0
LABEL org.opencontainers.image.rpc-contracts.version="0.1.0"
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY vendor/rpcdemo /app/rpcdemo
COPY app.py .
EXPOSE 50051 8080
CMD ["python", "/app/app.py"]
