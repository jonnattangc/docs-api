#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import boto3
    import base64
    import uuid
    import requests
    import unicodedata
    from .adocsrepo import ADocsRepo

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[AwsUtil] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


class Aws(ADocsRepo):
    access_key: str = os.environ.get('AWS_ACCESS_KEY', 'None')
    secret_key: str = os.environ.get('AWS_SECRET_KEY', 'None')
    aws_bucket: str = os.environ.get('AWS_BUCKET_NAME', 'None')
    aws_region: str = os.environ.get('AWS_REGION', 'us-east-1')
    s3_resource = None
    s3 = None

    def __init__(self):
        super().__init__()
        try:
            self.url_base = 'https://s3.' + self.aws_region + '.amazonaws.com/'
            session = boto3.Session(aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key)
            if session is None:
                raise Exception("AWS Session is None")
            logging.info("Session Available Resources: " + str(session.get_available_resources()))
            self.s3_resource = session.resource('s3')
            self.s3 = boto3.client('s3')
        except Exception as e:
            print("[__init__] ERROR AWS:", e)

    def __del__(self):
        self.s3_resource = None

    def process(self, subpath: str, json_data, method: str) -> tuple:
        http_code = 200
        data_response = None
        success_message = 'Servicio ejecutado exitosamente'
        no_found_message = 'Servicio no implementado o no encontrado'

        if method == 'POST':
            if subpath.find('upload') < 0:
                logging.info("Payload JSON :" + str(json_data))
            if subpath.find('read') >= 0:
                data_response, http_code = self.read_file(data=json_data)
            elif subpath.find('upload') >= 0:
                data_response, http_code = self.s3_uploader(request_data=json_data)
            else:
                data_response = {'statusCode': 404, 'status': no_found_message}
                http_code = 404
        elif method == 'GET':
            if subpath.find('test') >= 0:
                data_response, http_code = self.test_aws()
            else:
                data_response = {'statusCode': 404, 'status': no_found_message}
                http_code = 404
        else:
            data_response = {'statusCode': 404, 'status': no_found_message}
            http_code = 404

        return {'data': data_response, 'message': success_message}, http_code

    def get_implementation_name(self) -> str:
        return "Aws(v1.0.0)"

    def s3_uploader(self, request_data=None):
        data_response = {}
        http_code = 201
        m1 = time.monotonic()
        try:
            if request_data is None:
                raise Exception("Request data is None")
            name_file = str(request_data['name'])
            logging.info('[S3] Archivo a subir: ' + str(name_file))
            tmp_name_file: str = str(uuid.uuid4()) + '-' + name_file
            s3_name_file: str = str(request_data['folder']) + '/' + tmp_name_file
            logging.info('[S3] Ruta: ' + str(s3_name_file))

            data = str(request_data['fileb64'])
            data = data.replace('data:image/png;base64,', '')
            data = data.replace('data:application/pdf;base64,', '')

            file_path = os.path.join('/tmp/', str(tmp_name_file))
            file_content = base64.b64decode(data)
            with open(file_path, 'wb') as f:
                f.write(file_content)

            s3_bucket = self.s3_resource.Bucket(name=self.aws_bucket)
            s3_bucket.upload_file(Filename=file_path, Key=s3_name_file)

            md5_calculated = self.calculate_md5(file_content)
            logging.info('[S3] MD5: ' + str(md5_calculated))

            data_response = {
                'size_bytes': os.path.getsize(file_path),
                'md5': str(md5_calculated)
            }
            http_code = 201
            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception as e:
            print("[S3] ERROR AWS:", e)
            http_code = 403
            data_response = {'size_bytes': -1, 'md5': ''}
        diff = time.monotonic() - m1
        logging.info("[S3] Servicio Ejecutado en " + str(diff) + " sec.")
        return data_response, http_code

    def test_aws(self):
        retorno = {'serviceStatus': False}
        status = 200
        m1 = time.monotonic()
        try:
            retorno = {'serviceStatus': self.s3_resource is not None and self.s3 is not None}
        except Exception as e:
            print("[STATUS] ERROR AWS:", e)
            status = 403
        diff = time.monotonic() - m1
        logging.info("[STATUS] Servicio Ejecutado en " + str(diff) + " msec.")
        return retorno, status

    def search(self, json_data) -> tuple:
        msg = 'Servicio ejecutado correctamente'
        code_http = 200
        files_response: list = []
        files_list: list = []
        photos: list = self.get_photos()
        docs: list = self.get_docs()

        try:
            filters: list = []
            try:
                filters = json_data["filters"]
            except Exception:
                filters = []

            if filters is not None and len(filters) > 0:
                for f in filters:
                    filter_name: str = str(f['filter_name'])
                    comparator: str = str(f['comparation'])
                    if filter_name == 'mimeType' and comparator == '=':
                        filter_value = str(f['filter_value'])
                        if filter_value in ('image/png', 'image/jpeg'):
                            files_list.extend(photos)
                        elif filter_value == 'application/pdf':
                            files_list.extend(docs)
                        else:
                            files_list = []
                    elif filter_name == 'title' and comparator == 'contains':
                        filter_value: str = str(f['filter_value'])
                        for p in photos:
                            title: str = str(p['url']).split("/")[-1]
                            if title.find(filter_value) >= 0 and (title.endswith('.jpg') or title.endswith('.jpeg') or title.endswith('.png')):
                                files_list.append(p)
                        for d in docs:
                            title: str = str(d['url']).split("/")[-1]
                            if title.find(filter_value) >= 0 and title.endswith('.pdf'):
                                files_list.append(d)
                    else:
                        files_list = []

            for file in files_list:
                name_file: str = file['url']
                title: str = name_file.split("/")[-1]
                name_file = name_file.replace(' ', '%20')
                if title is not None and title != "":
                    value = {'title': title, 'url': name_file}
                    if value not in files_response:
                        files_response.append(value)

        except Exception as e:
            print("ERROR search_file():", e)
            code_http = 500
            msg = 'Error Message: ' + str(e)

        return {'data': files_response, 'message': msg}, code_http

    def list(self, json_data) -> tuple:
        http_code = 409
        data = {}
        m1 = time.monotonic_ns()
        try:
            photos = self.get_photos()
            docs = self.get_docs()
            data = {
                'photos': str(photos),
                'docs': str(docs)
            }
            http_code = 200
        except Exception as e:
            print("ERROR AWS:", e)
            http_code = 500
            data = {'status': 'Salto una excepcion !'}
        diff = time.monotonic_ns() - m1
        logging.info('Service Time Response in ' + str(diff) + ' nsec')
        return {'data': data, 'message': 'Servicio ejecutado correctamente'}, http_code

    def get_photos(self):
        elements = []
        m1 = time.monotonic_ns()
        try:
            if self.s3_resource is not None:
                for bucket in self.s3_resource.buckets.all():
                    for obj in bucket.objects.filter(Prefix='photos/'):
                        elements.append({'url': self.url_base + obj.bucket_name + '/' + obj.key})
        except Exception as e:
            print("[Photos] ERROR AWS:", e)
            elements = []
        diff = time.monotonic_ns() - m1
        logging.info("[Photos] AWS Time S3 Photos Response in " + str(diff) + " nsec.")
        return elements

    def get_docs(self):
        elements = []
        m1 = time.monotonic()
        try:
            if self.s3_resource is not None:
                for bucket in self.s3_resource.buckets.all():
                    for obj in bucket.objects.filter(Prefix='docs/'):
                        elements.append({'url': self.url_base + obj.bucket_name + '/' + obj.key})
        except Exception as e:
            print("[Docs] ERROR AWS:", e)
            elements = []
        diff = time.monotonic() - m1
        logging.info("[Docs] AWS Time S3 Docs Response in " + str(diff) + " sec.")
        return elements

    def clean_text(self, texto: str):
        text: str = unicodedata.normalize('NFD', texto)
        text = ''.join(char for char in text if unicodedata.category(char) != 'Mn')
        text = text.replace('ñ', 'n').replace('Ñ', 'N')
        text = text.lower()
        return text

    def read_file(self, data=None):
        element = None
        m1 = time.monotonic()
        code_http = 200
        try:
            if self.s3_resource is not None:
                for bucket in self.s3_resource.buckets.all():
                    if bucket.name.find(self.aws_bucket) < 0 and bucket.name != self.aws_bucket:
                        continue
                    logging.info('[Docs] Se busca en Bucket: ' + str(bucket.name))
                    for obj in bucket.objects.filter(Prefix='docs/'):
                        if obj.key is None or obj.key.endswith('/'):
                            continue
                        aws_file_name: str = self.clean_text(str(obj.key))
                        solicitude_file_name: str = self.clean_text(str(data['name_file']))
                        if aws_file_name.find(solicitude_file_name) >= 0 and aws_file_name.find(str(data['folder'])) >= 0:
                            url_file: str = self.url_base + obj.bucket_name + '/' + obj.key
                            response = requests.get(url_file, stream=True)
                            file_content = response.content
                            md5_calculated: str = self.calculate_md5(file_content)
                            if md5_calculated:
                                if md5_calculated != data['md5sum']:
                                    logging.error("MD5 NO Coinciden, Calculado: " + str(md5_calculated))
                                    code_http = 409
                                    element = None
                                    break
                            encoded_content = base64.b64encode(file_content)
                            element = {
                                'type': 'application/pdf',
                                'file_b64': encoded_content.decode('utf-8'),
                                'md5': md5_calculated,
                                'size_bytes': obj.size
                            }
                            break
        except Exception as e:
            print("[Docs] ERROR AWS:", e)
            element = None
            code_http = 500
        diff = time.monotonic() - m1
        logging.info("[Docs] AWS Time S3 Docs Response in " + str(diff) + " sec.")
        return element, code_http
