FROM python:3.8-slim-buster

WORKDIR /app

RUN pip3 install fastapi
RUN pip install fastapi uvicorn

COPY . .

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
