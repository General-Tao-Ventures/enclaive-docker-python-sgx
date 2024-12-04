# mariadb with patches

FROM enclaive/gramine-os:jammy-7e9d6925

RUN apt-get update \
    && apt-get install -y  wget build-essential python3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/

COPY ./app /app/
COPY ./app.manifest.template ./entrypoint.sh /app/


RUN gramine-argv-serializer "/usr/bin/python3" "/app/main.py" > args.txt &&\
    gramine-manifest -Darch_libdir=/lib/x86_64-linux-gnu app.manifest.template app.manifest &&\
    gramine-sgx-sign --key "$SGX_SIGNER_KEY" --manifest app.manifest --output app.manifest.sgx

EXPOSE 3306/tcp

ENTRYPOINT [ "/app/entrypoint.sh" ]

# Copy SSL certificates into the image
COPY certs/cert.pem /app/cert.pem
COPY certs/key.pem /app/key.pem

# Expose port 8000
EXPOSE 8888

# Start the server with SSL
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888", "--ssl-keyfile", "/app/key.pem", "--ssl-certfile", "/app/cert.pem"]
