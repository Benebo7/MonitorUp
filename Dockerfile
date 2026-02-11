# 1. Base: Começa com um Linux leve que já tem Python 3.10 instalado
FROM python:3.10-slim

# 2. Configura variáveis de ambiente pra o Python não criar arquivos .pyc e logs aparecerem na hora
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Cria a pasta de trabalho dentro do container (como se fosse um mkdir)
WORKDIR /app

# 4. Copia SÓ o requirements.txt primeiro (Estratégia de Cache Inteligente)
# Se você mudar seu código, mas não mudar as libs, o Docker não precisa reinstalar tudo.
COPY requirements.txt .

# 5. Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copia o resto do seu código para dentro da pasta /app
COPY . .

# 7. Comando para iniciar sua API quando o container nascer
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]