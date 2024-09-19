# 使用 Python 官方轻量镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制 requirements.txt 并安装依赖
COPY ./app/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 复制项目文件
COPY ./app /app

# 暴露端口
EXPOSE 8000

# 运行 FastAPI 应用
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
