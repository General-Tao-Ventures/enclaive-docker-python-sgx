# mariadb with patches

FROM enclaive/gramine-os:jammy

RUN apt-get update \
    && apt-get install -y wget build-essential python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

RUN gramine-argv-serializer "/usr/bin/python3" "/app/app/main.py" > args.txt &&\
    gramine-manifest -Darch_libdir=/lib/x86_64-linux-gnu app.manifest.template app.manifest &&\
    gramine-sgx-sign --key "$SGX_SIGNER_KEY" --manifest app.manifest --output app.manifest.sgx

EXPOSE 8888

ENTRYPOINT [ "/app/entrypoint.sh" ]
