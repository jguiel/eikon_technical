FROM python:3.10-slim-buster
WORKDIR /api_cli

COPY requirements-pip3.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements-pip3.txt
# RUN pip install click
RUN apt-get update && apt-get install -y curl

COPY . .

# Keep container open for CLI commands
CMD tail -f /dev/null