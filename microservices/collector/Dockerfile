FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt 

# 拷贝代码
COPY ./src/ ./src/
COPY .env ./.env
# COPY ./src/trends.db ./src/trends.db

# 复制启动脚本
COPY bin/start.sh /app/bin/start.sh
RUN chmod +x /app/bin/start.sh

WORKDIR /app/src
CMD ["sh", "/app/bin/start.sh"]