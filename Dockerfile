# mariadb with patches

FROM enclaive/gramine-os:jammy-7e9d6925

RUN apt-get update \
    && apt-get install -y wget build-essential python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

# Copy requirements first to leverage Docker cache
COPY ./app/requirements.txt /app/
RUN pip3 install -r requirements.txt
RUN pip3 install python-dotenv

# Copy the rest of the application
COPY ./app /app/
COPY ./app.manifest.template ./entrypoint.sh /app/

# Copy SSL certificates into the image
COPY certs/cert.pem /app/cert.pem
COPY certs/key.pem /app/key.pem

# Create a directory for environment files
RUN mkdir -p /app/config

RUN gramine-argv-serializer "/usr/bin/python3" "/app/main.py" > args.txt &&\
    gramine-manifest -Darch_libdir=/lib/x86_64-linux-gnu app.manifest.template app.manifest &&\
    gramine-sgx-sign --key "$SGX_SIGNER_KEY" --manifest app.manifest --output app.manifest.sgx

EXPOSE 8888

ENTRYPOINT [ "/app/entrypoint.sh" ]
