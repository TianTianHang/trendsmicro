FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 拷贝代码
COPY ./src/ ./src/
COPY .env ./.env
WORKDIR /app/src
CMD ["uvicorn", "main:app","--host","0.0.0.0","--port","8000"]
