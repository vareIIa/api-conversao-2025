# Usando uma imagem base leve com Python
FROM python:3.10-slim

# Diretório de trabalho dentro do contêiner
WORKDIR /app

# Copiar os arquivos do projeto para o contêiner
COPY . /app

# Instalar as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Expõe a porta que o Flask usa (5000 por padrão)
EXPOSE 5000

# Define variáveis de ambiente padrão
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=5000

# Comando para rodar o Flask
CMD ["python", "-u", "app.py"]