FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
COPY collector/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝代码
COPY collector/src/ ./src/
COPY config/ ./config/

CMD ["python", "src/main.py"]