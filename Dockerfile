FROM python:3.14-rc-slim AS builder

WORKDIR /src

COPY requirements.txt .

RUN apt-get update -y && \
    apt-get install -y build-essential && \
    apt-get install -y libssl-dev && \
    apt-get install -y libffi-dev && \
    apt-get install -y python3-dev && \
    apt-get install -y cargo  && \
    pip wheel --no-cache-dir --wheel-dir=/src/dist -r requirements.txt

FROM python:3.14-rc-slim

LABEL VERSION=1.0
LABEL DESCRIPCION="API para documentos"

ENV TZ 'UTC'
ENV HOST_BD ''
ENV USER_BD ''
ENV PASS_BD ''
ENV SERVER_API_KEY ''
ENV AES_KEY ''

ENV FLASK_APP app
ENV FLASK_DEBUG development

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan


RUN cd /home/jonnattan && \
    mkdir -p /home/jonnattan/.local/bin && \
    export PATH=$PATH:/home/jonnattan/.local/bin && \
    chmod -R 755 /home/jonnattan && \
    chown -R jonnattan:jonnattan /home/jonnattan

WORKDIR /home/jonnattan

USER jonnattan

COPY . .

COPY --from=builder --chown=10100:10101 --chmod=755 /src/dist /home/jonnattan/dist

RUN pip install --no-cache-dir --no-index --find-links=file:///home/jonnattan/dist -r requirements.txt

WORKDIR /home/jonnattan/app

EXPOSE 8080

CMD [ "python", "http-server.py", "8080"]
    
