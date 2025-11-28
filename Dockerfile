FROM python:3.9-slim

WORKDIR /app

# 复制并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制主代码
COPY bot.py .

# 启动命令
CMD ["python", "bot.py"]