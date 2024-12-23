FROM python:3.14-rc-slim AS Builder

WORKDIR /src

COPY requirements.txt /src/requirements.txt

RUN apt-get update -y && \
    apt-get install -y build-essential && \
    apt-get install -y libssl-dev && \
    apt-get install -y libffi-dev && \
    apt-get install -y python3-dev && \
    apt-get install -y cargo

RUN pip wheel --no-cache-dir --wheel-dir=/src/dist -r requirements.txt && \
    ls -la /src/dist

    # pip install --no-cache-dir --no-index --find-links=/src/wheelhouse .

FROM python:3.14.0a2-alpine3.21

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

RUN adduser -h /home/jonnattan -u 10100 -g 10101 --disabled-password jonnattan  && \
    cd /home/jonnattan && \
    mkdir -p /home/jonnattan/.local/bin && \
    export PATH=$PATH:/home/jonnattan/.local/bin && \
    chmod -R 755 /home/jonnattan  && \
    chown -R jonnattan:jonnattan /home/jonnattan

WORKDIR /home/jonnattan

COPY . /home/jonnattan

COPY --from=Builder /src/dist /home/jonnattan/dist

RUN pip install -r requirements.txt

WORKDIR /home/jonnattan/app

USER jonnattan

EXPOSE 8091

CMD [ "python", "http-server.py", "8091"]
