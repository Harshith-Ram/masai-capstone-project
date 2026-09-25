FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV MOCK_LLM=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt
# CPU-only torch avoids pulling multi-gigabyte CUDA wheels that sentence-transformers would otherwise resolve.
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --default-timeout=120 --retries 5 -r /app/requirements.txt

COPY . /app

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
