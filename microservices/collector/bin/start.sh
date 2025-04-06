#!/bin/bash

# 启动FastAPI服务器
uvicorn main:app --host 0.0.0.0 --port 8000 &

# 启动Dramatiq worker
dramatiq core.jobs --processes 1 --threads 8

# 等待所有后台进程
wait