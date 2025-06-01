#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import boto3
    import base64
    import uuid

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[AwsUtil] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class Aws() :
    url_base : str = 'https://s3.__AWS_REGION__.amazonaws.com/'
    access_key : str = os.environ.get('AWS_ACCESS_KEY','None')
    secret_key : str = os.environ.get('AWS_SECRET_KEY','None')
    bucket_name : str = 'jonnattan.com-storage'
    s3_resource = None
    s3 = None
    root  : str = '.'

    # ==============================================================================
    # Constructor
    # ==============================================================================
    def __init__(self, root = str(ROOT_DIR), region='us-east-1') :
        self.url_base = self.url_base.replace('__AWS_REGION__', region)
        try :
            self.root = str(root)
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
        self.url_base = 'https://s3.__AWS_REGION__.amazonaws.com/'
        del self.s3_resource
        self.s3_resource = None

    # ==============================================================================
    # Procesa todos los request 
    # ==============================================================================
    def request_process(self, request, action : str ) :
        logging.info("Reciv " + str(request.method) + " Acción: /docs/s3/" + action )
        #logging.info("Reciv Data: " + str(request.data) )
        #logging.info("Reciv Header : " + str(request.headers) )
        path : str = action.lower().strip()
        data = {'status':'Error ocurrido'}
        status = 409
        if action != None :   
            if path.find('list') >= 0 :
                return self.s3ObjectList()
            elif path.find('contents') >= 0 :
                return self.s3ObjectList()
            elif path.find('upload') >= 0 :
                return self.s3Uploader( request )
            else :
                data = {'status':'No Implementedo'}
                status = 409
        return data, status
    
    def s3Uploader( self, request ) :
        data = {'ref': 'Servicio Ejecutado exitosamente'}
        code = 200
        m1 = time.monotonic_ns()
        try :
            request_data = request.get_json()
            name_file = str(request_data['name'])
            name_file = 'photos/' + str(uuid.uuid4()) + '-' + name_file

            data = str(request_data['data'])
            data = data.replace('data:image/png;base64,','')

            name = 'test.png'
            file_path = os.path.join(self.root, 'static')
            file_path = os.path.join(file_path, 'images')
            file_path = os.path.join(file_path, str(name))

            file = open(file_path, 'wb')
            file.write( base64.b64decode((data) ))
            file.close()

            logging.info('[S3] Archivo a subir: ' + str(file_path))
            logging.info('[S3] Nombre: ' + str(name_file))
            
            s3_bucket = self.s3_resource.Bucket(name=self.bucket_name)
            s3_bucket.upload_file( Filename=file_path, Key=name_file )
            data = { 
                'url': str(self.url_base) + str(self.bucket_name) + '/' + str(name_file),
                'msg': 'Servicio ejecutado exitosamente',
                'code': 0
            }


        except Exception as e:
            print("[S3] ERROR AWS:", e)
            code = 403
            data = { 'ref': 'Error: ' + str(e) }

        diff = time.monotonic_ns() - m1
        logging.info("[S3] Servicio Ejecutado en " + str(diff) + " nsec." )
        return data, code 


    def testAws( self ) :
        retorno = {'valid': False }
        status = 200
        m1 = time.monotonic()
        try :
            retorno = {'valid': self.s3_resource != None and self.s3 != None } 
        except Exception as e:
            print("[STATUS] ERROR AWS:", e)
            status = 500
        diff = time.monotonic() - m1
        logging.info("[STATUS] Servicio Ejecutado en " + str(diff) + " msec." )
        return retorno, status 
    
    # ==============================================================================
    # Lista de cosas en s3
    # ==============================================================================
    def s3ObjectList( self ) :
        http_code = 409
        data = {}
        m1 = time.monotonic_ns()
        try :
            photos = self.getPhotos()
            docs = self.getDocs()
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
    def getPhotos( self ) :
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
    def getDocs( self ) :
        elements = []
        m1 = time.monotonic_ns()
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

        diff = time.monotonic_ns() - m1
        logging.info("[Docs] AWS Time S3 Docs Response in " + str(diff) + " nsec." )
        return elements
