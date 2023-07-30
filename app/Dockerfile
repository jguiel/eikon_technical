FROM python:3.10-slim-buster

WORKDIR /app
COPY requirements-pip3.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements-pip3.txt

COPY . /app/
