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
    import hashlib

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[AwsUtil] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Aws() :
    access_key : str = os.environ.get('AWS_ACCESS_KEY','None')
    secret_key : str = os.environ.get('AWS_SECRET_KEY','None')
    aws_bucket : str = os.environ.get('AWS_BUCKET_NAME','None')
    aws_region : str = os.environ.get('AWS_REGION','us-east-1')
    url_base : str = 'https://s3.' + aws_region + '.amazonaws.com/'
    api_key : str = None
    s3_resource = None
    s3 = None
    root  : str = '.'

    # ==============================================================================
    # Constructor
    # ==============================================================================
    def __init__(self, root = str(ROOT_DIR)) :
        try :
            self.root = root
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
            session = boto3.Session(aws_access_key_id=self.access_key, aws_secret_access_key=self.secret_key)
            if session is None :
                raise Exception("AWS Session is None")
            else :
                logging.info("Session Available Resources: " + str(session.get_available_resources()) )
                self.s3_resource = session.resource('s3')
                self.s3 = boto3.client('s3')
        except Exception as e:
            print("[__init__] ERROR AWS:", e)

    # ==============================================================================
    # Destructor
    # ==============================================================================
    def __del__(self):
        del self.s3_resource
        self.s3_resource = None

    # ==============================================================================
    # Procesa todos los request 
    # ==============================================================================
    def request_process(self, request, action : str ) :
        http_code  = 200
        data_response = None
        success_message : str = 'Servicio ejecutado exitosamente'
        no_found_message : str = 'Servicio no implementado o no encontrado'
        response =  {"message" : success_message, "data": data_response}
        json_data = None
        logging.info("Reciv " + str(request.method) + " Acción: /docs/s3/" + action )

        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key == None :
            response = {"message" : "Api key no encontrada", "data": data_response }
            http_code  = 401
            return  response, http_code
        if str(rx_api_key) != str(self.api_key) :
            response = {"message" : "Api key no es valida", "data": data_response }
            http_code  = 401
            return  response, http_code
        
        path : str = None 
        if action != None : 
            path = action.lower().strip()

        if request.method == 'POST' :
            request_data = request.get_json()
            request_type = None
            data_rx = None
            try :
                request_type = request_data['type']
            except Exception as e :
                request_type = None
            try :
                data_rx = request_data['data']
            except Exception as e :
                data_rx = None

            if request_type != None :
                # encrypted or inclear
                if data_rx != None and str(request_type) == 'encrypted' :
                    data_cipher = str(data_rx)
                    logging.info('Data Encrypt: ' + str(data_cipher) )
                    data_clear = self.cipher.aes_decrypt(data_cipher)
                    logging.info('Data EnClaro: ' + str(data_clear) )
                    json_data = json.dumps(data_clear)
                else: 
                    json_data = data_rx
            else: 
                    json_data = data_rx
            
            if path.find('upload') < 0 :
                logging.info("Payload JSON :" + str(json_data) )
            
            if path.find('search') >= 0 :
                data_response, http_code = self.search_file( json_data )
            if path.find('read') >= 0 :
                data_response, http_code = self.read_file( data = json_data )
            elif path.find('upload') >= 0 :
                data_response, http_code =  self.s3_uploader( request_data = json_data )
            else :
                data_response = {'statusCode' : 404, 'status': no_found_message}
                http_code = 404
        elif request.method == 'GET' :
            if path.find('list') >= 0 :
                data_response, http_code = self.s3_object_list()
            elif path.find('test') >= 0 :
                data_response, http_code = self.test_aws()
            else :
                data_response = {'statusCode' : 404, 'status': no_found_message}
                http_code = 404
        else :
            data_response = {'statusCode' : 404, 'status': no_found_message}
            http_code = 404
        response = {"data": data_response, "message" : success_message }
        return  response, http_code
    
    def s3_uploader( self, request_data = None ) :
        data_response = {}
        http_code = 201
        m1 = time.monotonic()
        try :
            if request_data == None :
                raise Exception("Request data is None")
            name_file = str(request_data['name'])
            logging.info('[S3] Archivo a subir: ' + str(name_file))
            tmp_name_file : str = str(uuid.uuid4()) + '-' + name_file
            logging.info('[S3] Ruta temp: /tmp/' + str(tmp_name_file))
            s3_name_file : str = str(request_data['folder']) + '/' + tmp_name_file
            logging.info('[S3] Ruta: ' + str(s3_name_file))

            data = str(request_data['fileb64'])
            data = data.replace('data:image/png;base64,','')
            data = data.replace('data:application/pdf;base64,','')

            file_path = os.path.join('/tmp/', str(tmp_name_file))
            file = open(file_path, 'wb')
            file_content = base64.b64decode((data) )
            file.write(file_content)
            file.close()
            
            s3_bucket = self.s3_resource.Bucket(name=self.aws_bucket)
            s3_bucket.upload_file( Filename=file_path, Key=s3_name_file )

            md5_calculated = self.calculate_md5(file_content)
            logging.info('[S3] MD5: ' + str(md5_calculated))

            data_response = {
                'size_bytes': os.path.getsize(file_path),
                'md5': str(md5_calculated)
            }
            http_code = 201
            # se borra el archivo temporal
            if os.path.exists(file_path):
                os.remove(file_path)    

        except Exception as e:
            print("[S3] ERROR AWS:", e)
            http_code = 403
            data_response = { 'size_bytes': -1, 'md5': '' }
        diff = time.monotonic() - m1
        logging.info("[S3] Servicio Ejecutado en " + str(diff) + " sec." )
        return data_response, http_code 


    def test_aws( self ) :
        retorno = {'serviceStatus': False }
        status = 200
        m1 = time.monotonic()
        try :
            retorno = {'serviceStatus': self.s3_resource != None and self.s3 != None } 
        except Exception as e:
            print("[STATUS] ERROR AWS:", e)
            status = 403
        diff = time.monotonic() - m1
        logging.info("[STATUS] Servicio Ejecutado en " + str(diff) + " msec." )
        return retorno, status 
    
    def search_file (self, json_data ) :
        msg = 'Servicio ejecutado correctamente'
        code_http = 200
        files_response  : list = []
        files_list : list = []
        photos : list = self.get_photos()
        docs : list = self.get_docs()

        folder_name : str = json_data["folder_id"]
        only_id : bool = False

        try:
            filters : list = []
            try :
                filters = json_data["filters"]
            except Exception as e :
                filters = []
            
            if filters != None and len(filters) > 0 :
                for f in filters :
                    filter_name : str = str(f['filter_name'])
                    comparator : str = str(f['comparation'])
                    if filter_name == 'mimeType' and comparator == '=' :
                        filter_value = str(f['filter_value'])
                        if filter_value == 'image/png' or filter_value == 'image/jpeg' :
                            files_list.extend( photos )
                        elif filter_value == 'application/pdf' :
                            files_list.extend( docs )
                        else :
                            files_list = []   
                    elif filter_name == 'title' and comparator == 'contains' :
                        filter_value : str = str(f['filter_value'])
                        for p in photos :
                            title : str = str(p['url']).split("/")[-1]
                            if title.find(filter_value) >= 0 and ( title.endswith('.jpg') >= 0 or title.endswith('.jpeg') >= 0 or title.endswith('.png') >= 0) :
                                files_list.append( p )
                        for d in docs :
                            title : str = str(d['url']).split("/")[-1]
                            if title.find(filter_value) >= 0 and title.endswith('.pdf') >= 0:
                                files_list.append( d )  
                    else :
                        files_list = []         

            for file in files_list : 
                name_file : str = file['url']
                title : str = name_file.split("/")[-1]
                name_file = name_file.replace(' ', '%20')       
                if title != None and title != "" : 
                    value = { 'title': title, 'url': name_file }
                    if value in files_response :
                        continue
                    else :  
                        files_response.append( value )
                
        except Exception as e :
           print("ERROR search_file():", e)
           code_http = 500
           msg = 'Error Message: ' + str(e)
           files = []
        
        response = {
            'msg': msg,
            'files': files_response
        }
        return response, code_http

    # ==============================================================================
    # Lista de cosas en s3
    # ==============================================================================
    def s3_object_list( self ) :
        http_code = 409
        data = {}
        m1 = time.monotonic_ns()
        try :
            photos = self.get_photos()
            docs = self.get_docs()
            data = {
                'photos' : str(photos),
                'docs' : str(docs)
            }
            http_code = 200
        except Exception as e:
            print("ERROR AWS:", e)
            http_code = 500
            data = { 'status': 'Salto una excepcion !' }

        diff = time.monotonic_ns() - m1
        logging.info('Service Time Response in ' + str(diff) + ' nsec' )
        return data, http_code 
    # ==============================================================================
    # Lista de fotos en s3
    # ==============================================================================
    def get_photos( self, ) :
        elements = []
        m1 = time.monotonic_ns()
        try :
            if self.s3_resource != None :
                logging.info('[Photos] s3_resource: ' + str(self.s3_resource) )
                for bucket in self.s3_resource.buckets.all():
                    logging.info('[Photos] Bucket: ' + bucket.name)
                    #contents = s3.Bucket(bucket.name)
                    for obj in bucket.objects.filter(Prefix='photos/') :
                        logging.info('[Photos] Bucket: ' + obj.bucket_name + ' Key: ' + obj.key)
                        elements.append({'url' : self.url_base + obj.bucket_name + '/' + obj.key })
        except Exception as e:
            print("[Photos] ERROR AWS:", e)
            elements = []

        diff = time.monotonic_ns() - m1
        logging.info("[Photos] AWS Time S3 Photos Response in " + str(diff) + " nsec." )
        return elements 
    # ==============================================================================
    # Lista de documentos en s3
    # ==============================================================================
    def get_docs( self, ) :
        elements = []
        m1 = time.monotonic()
        try :
            if self.s3_resource != None :
                logging.info('[Photos] s3_resource: ' + str(self.s3_resource) )
                for bucket in self.s3_resource.buckets.all():
                    logging.info('[Docs] Bucket: ' + bucket.name)
                    #contents = s3_resource.Bucket(bucket.name)
                    for obj in bucket.objects.filter(Prefix='docs/') :
                        logging.info('[Docs] Bucket: ' + obj.bucket_name + ' Key: ' + obj.key)
                        elements.append({'url' : self.url_base + obj.bucket_name + '/' + obj.key })
        except Exception as e:
            print("[Docs] ERROR AWS:", e)
            elements = []

        diff = time.monotonic() - m1
        logging.info("[Docs] AWS Time S3 Docs Response in " + str(diff) + " sec." )
        return elements

    def read_file( self, data = None ) :
        element = None
        m1 = time.monotonic()
        code_http = 200
        try :
            if self.s3_resource != None :
                logging.info('[Docs] s3_resource: ' + str(self.s3_resource) )
                for bucket in self.s3_resource.buckets.all():
                    if bucket.name.find(self.aws_bucket) < 0 and bucket.name != self.aws_bucket :
                        logging.info('[Docs] Bucket: ' + str(bucket.name) + ' descartado.')
                        continue
                    logging.info('[Docs] Se busca en Bucket: ' + str(bucket.name))
                    for obj in bucket.objects.filter(Prefix='docs/') :
                        if obj.key == None or obj.key.endswith('/'):
                            continue
                        logging.info('[Docs] File Solicitado: ' + str(data['name_file']) + ' y Encontrado: ' + obj.key)
                        if str(obj.key).find(str(data['name_file'])) >= 0 and str(obj.key).find(str(data['folder'])) >= 0 :
                            url_file : str = self.url_base + obj.bucket_name + '/' + obj.key
                            response = requests.get(url_file, stream=True)
                            file_content = response.content
                            md5_calculated = self.calculate_md5(file_content)
                            if md5_calculated :
                                if md5_calculated != data['md5sum'] :
                                    logging.error("MD5 NO Coinciden, Calculado: " + str(md5_calculated))
                                    logging.error("Contenido: " + str(response.content))
                                    code_http = 409
                                    element = None
                                    break
                            # Codificar el contenido a Base64
                            encoded_content = base64.b64encode(file_content)
                            element = {
                                'type' : 'application/pdf',
                                'file_b64' : encoded_content.decode('utf-8'),
                                'size_bytes' : obj.size
                            }
                            #logging.info('[Docs] Encontrado!!!!!!! URL: ' + str(element))
                            break
        except Exception as e:
            print("[Docs] ERROR AWS:", e)
            element = None
            code_http = 500

        diff = time.monotonic() - m1
        logging.info("[Docs] AWS Time S3 Docs Response in " + str(diff) + " sec." )
        return element, code_http

    def calculate_md5(self, data_bytes):
        if data_bytes is None:
            return None
        md5_hash = hashlib.md5()
        md5_hash.update(data_bytes)
        return md5_hash.hexdigest()