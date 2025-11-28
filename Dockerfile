FROM python:3.9-slim

WORKDIR /app

# --- 核心修改：直接在这里安装，不依赖 requirements.txt 文件 ---
RUN pip install --no-cache-dir python-telegram-bot volcengine-python-sdk
# -------------------------------------------------------

COPY bot.py .

CMD ["python", "bot.py"]
