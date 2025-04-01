FROM python:3.10-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y gcc wget unzip && rm -rf /var/lib/apt/lists/*



# 安装Python依赖
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 拷贝代码
COPY ./src/ ./src/

# 下载并解压国家边界数据
RUN mkdir -p /app/src/data && \
    wget https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip -O /tmp/countries.zip && \
    unzip /tmp/countries.zip -d /app/src/data && \
    rm /tmp/countries.zip

COPY .env ./.env
# COPY ./src/query.db ./src/query.db
WORKDIR /app/src
CMD ["python", "main.py"]
