#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import json
    from flask import jsonify
    import base64
    from PyPDF2 import PdfReader

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


ROOT_DIR = os.path.dirname(__file__)

class ApiDocs () :
    pdf_manager = None
    api_pey = None
    pdf_path = None
    def __init__(self, root_dir : str = str(ROOT_DIR)) :
        try:
            self.pdf_path = root_dir + '/static/docs'
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
            
        except Exception as e :
            print("ERROR :", e)
            self.pdf_path = None
            self.api_key = None
            self.pdf_manager = None

    def __del__(self):
        self.pdf_path = None
        self.api_key = None
        self.pdf_manager = None

    def request_process(self, request, subpath ) :
        message = "Servicio ejecutado exitosamente"
        http_code  = 200
        data_response = None
        response =  {"message" : message, "data": data_response}
        json_data = None
        logging.info("Reciv " + str(request.method) + " Contex: /docs/api/" + str(subpath) )
        #logging.info("Reciv Header :\n" + str(request.headers) )
        #logging.info("Reciv Data: " + str(request.data) )
        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key == None :
            response = {"message" : "No autorizado", "data": data_response }
            http_code  = 401
            return  response, http_code
        if str(rx_api_key) != str(self.api_key) :
            response = {"message" : "No autorizado", "data": data_response }
            http_code  = 401
            return  response, http_code
        
        if subpath == None or subpath == '' :
            response = {"data": None, "message" : 'Metodo no disponible' }
            http_code = 404
        else :
            if request.method == 'GET' :
                if str(subpath).find('pdf2txt') >= 0 :
                    file_dir : str = self.pdf_path + '/Las_virtudes_del_grado_de_comp.pdf'
                    text, http_code = self.pdf_to_text( file_dir )
                    response = {"data": str(text), "message" : 'Metodo ejecutado correctamente' }   
            elif request.method == 'POST' :
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
                    if data_rx != None and str(request_type) == 'encrypted' and request.method == 'POST' :
                        data_cipher = str(data_rx)
                        logging.info('Data Encrypt: ' + str(data_cipher) )
                        data_clear = self.cipher.aes_decrypt(data_cipher)
                        logging.info('Data EnClaro: ' + str(data_clear) )
                        json_data = json.dumps(data_clear)
                    else: 
                        json_data = data_rx
                else: 
                        json_data = data_rx
                logging.info("JSON :" + str(json_data) )
                if str(subpath).find('pdf2txt') >= 0 :
                    file_dir : str = self.pdf_path + 'Las_virtudes_del_grado_de_comp.pdf'
                    text, http_code = self.pdf_to_text( file_dir )
                    response = {"data": str(text), "message" : 'Metodo ejecutado correctamente' }             
            else :
                response = {"data": None, "message" : 'Metodo no disponible' }
                http_code = 404
            
        
        response = {"data": data_response, "message" : message }
        return  response, http_code

    def pdf_to_text(self, file_path: str ):
        http_code  = 200
        document : str = ''
        try:
            logging.info('Open: ' + str(file_path) )
            reader = PdfReader(file_path)
            number_of_pages = len(reader.pages)
            logging.info('number_of_pages: ' + str(number_of_pages) )
            for page_num in range(number_of_pages):
                page = reader.pages[page_num]
                if page != None :
                    document += str(page.extract_text())
        except Exception as e :
            print("ERROR pdf_to_text(): ", e)
            http_code  = 500
            document = str(e)
        logging.info('document: ' + str(document) )
        return document, http_code