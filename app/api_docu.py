#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import json
    from flask import jsonify
    import base64
    from PyPDF2 import PdfReader
    from adocsrepo import ADocsRepo

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


ROOT_DIR = os.path.dirname(__file__)

class ApiDocs (ADocsRepo) :
    pdf_manager = None
    pdf_path = None
    def __init__(self, root_dir : str = str(ROOT_DIR)) :
        try:
            self.pdf_path = root_dir + '/static/docs'

        except Exception as e :
            print("ERROR :", e)
            self.pdf_path = None
            self.pdf_manager = None

    def __del__(self):
        self.pdf_path = None
        self.pdf_manager = None

    def process(self, subpath: str, json_data: str, method: str)  -> {dict, int} :
        message = "Servicio ejecutado exitosamente"
        http_code  = 200
        data_response = None
        if method == 'GET' :
            if str(subpath).find('pdf2txt') >= 0 :
                file_dir : str = self.pdf_path + '/Las_virtudes_del_grado_de_comp.pdf'
                text, http_code, message = self.pdf_to_text( file_dir )
                data_response = { "document": str(text) }  
            else :
                data_response = None
                http_code = 404     
        elif method == 'POST' :
            if str(subpath).find('pdf2txt') >= 0 :
                file_dir : str = self.pdf_path + 'Las_virtudes_del_grado_de_comp.pdf'
                text, http_code, message = self.pdf_to_text( file_dir )
                data_response = { "document": str(text) }    
            else :
                data_response = None
                http_code = 404              
        else :
            data_response = None
            http_code = 404        
        response = {"data": data_response, "message" : message }
        return  response, http_code

    def get_implementation_name(self) -> str:
        return f"ApiDocs(v1.0.0)"

    def search(self, json_data: str)  -> {dict, int} :
        response = {"data": None, "message" : 'Not found' }
        return  response, 404

    def pdf_to_text(self, file_path: str ):
        http_code  = 200
        document : str = ''
        message : str = "Documento procesado correctamente"
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
            document = None
            message = str(e)
        logging.info('document: ' + str(document) )
        return document, http_code, message