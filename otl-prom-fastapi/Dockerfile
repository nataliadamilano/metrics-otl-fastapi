FROM python:3.10.2-slim-buster

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY app.py .

EXPOSE 6060

ENTRYPOINT [ "python","app.py" ]