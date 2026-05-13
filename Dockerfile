FROM python:3.14-rc-slim AS builder
WORKDIR /src
COPY requirements.txt .
RUN apt-get update -y && \
    apt-get install -y build-essential libssl-dev libffi-dev python3-dev cargo && \
    pip wheel --no-cache-dir --wheel-dir=/src/dist -r requirements.txt

FROM python:3.14-rc-slim

LABEL MAINTAINER="Jonnattan Griffiths"
LABEL VERSION=1.0
LABEL DESCRIPCION="API para leer archivos pdfs remotos"

ENV TZ='UTC'
ENV USER=jonnattan
ENV HOST_BD=''
ENV USER_BD=''
ENV PASS_BD=''
ENV APPKEY=''
ENV FLASK_APP=app
ENV FLASK_DEBUG=production
ENV PATH="/home/jonnattan/.local/bin:${PATH}"
ENV PYTHONPATH="/home/jonnattan/.local/lib/python3.14/site-packages"

RUN addgroup --gid 10101 jonnattan && \
    adduser --home /home/jonnattan --uid 10100 --gid 10101 --disabled-password jonnattan

WORKDIR /home/jonnattan

USER jonnattan

COPY --from=builder --chown=10100:10101 /src/dist /home/jonnattan/dist

COPY --chown=10100:10101 requirements.txt /home/jonnattan

RUN pip install --user --no-cache-dir --no-index --find-links=file:///home/jonnattan/dist -r requirements.txt

WORKDIR /home/jonnattan/app

COPY --chown=10100:10101 ./app .

EXPOSE 8095

CMD [ "python", "main.py", "8095"]