FROM ubuntu:jammy

RUN apt-get update \
    && apt-get install -y wget build-essential python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8888

ENTRYPOINT [ "python3", "app/main.py" ]