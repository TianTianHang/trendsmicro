FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc openssl && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 拷贝代码
COPY ./src/ ./src/
# 生成私钥和公钥
RUN openssl genpkey -algorithm RSA -out ./private_key.pem
RUN openssl rsa -pubout -in ./private_key.pem -out ./public_key.pem
COPY .env ./.env
COPY ./src/user.db ./src/user.db
WORKDIR /app/src
CMD ["python", "main.py"]
