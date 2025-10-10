FROM python:3.11-slim

# Variabili d'ambiente
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Installa dipendenze di sistema
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Directory di lavoro
WORKDIR /app

# Copia requirements e installa dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copia il codice
COPY src ./src
COPY data ./src/wlkg/data
COPY config.yml ./config.yml



# Crea utente non-root
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Esponi porta
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Cambia directory di lavoro a src
WORKDIR /app/src

# Comando di avvio
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]