#!/usr/bin/python

try:
    import logging
    import sys
    import os
    from PyPDF2 import PdfReader
    from .adocsrepo import ADocsRepo

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[ApiDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

# Apunta al directorio app/, un nivel arriba de services/
APP_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ApiDocs(ADocsRepo):
    pdf_path = None

    def __init__(self):
        super().__init__()
        try:
            self.pdf_path = os.path.join(APP_DIR, 'static', 'docs')
        except Exception as e:
            print("ERROR :", e)
            self.pdf_path = None

    def __del__(self):
        self.pdf_path = None

    def process(self, subpath: str, json_data, method: str) -> tuple:
        message = "Servicio ejecutado exitosamente"
        http_code = 200
        data_response = None

        if method == 'GET':
            if str(subpath).find('pdf2txt') >= 0:
                file_dir: str = os.path.join(self.pdf_path, 'Las_virtudes_del_grado_de_comp.pdf')
                text, http_code, message = self.pdf_to_text(file_dir)
                data_response = {"document": str(text)}
            else:
                data_response = None
                http_code = 404
        elif method == 'POST':
            if str(subpath).find('pdf2txt') >= 0:
                file_dir: str = os.path.join(self.pdf_path, 'Las_virtudes_del_grado_de_comp.pdf')
                text, http_code, message = self.pdf_to_text(file_dir)
                data_response = {"document": str(text)}
            else:
                data_response = None
                http_code = 404
        else:
            data_response = None
            http_code = 404

        return {'data': data_response, 'message': message}, http_code

    def get_implementation_name(self) -> str:
        return "ApiDocs(v1.0.0)"

    def search(self, json_data) -> tuple:
        return {'data': None, 'message': 'Not found'}, 404

    def list(self, json_data) -> tuple:
        return {'data': None, 'message': 'Not found'}, 404

    def pdf_to_text(self, file_path: str):
        http_code = 200
        document: str = ''
        message: str = "Documento procesado correctamente"
        try:
            logging.info('Open: ' + str(file_path))
            reader = PdfReader(file_path)
            number_of_pages = len(reader.pages)
            logging.info('number_of_pages: ' + str(number_of_pages))
            for page_num in range(number_of_pages):
                page = reader.pages[page_num]
                if page is not None:
                    document += str(page.extract_text())
        except Exception as e:
            print("ERROR pdf_to_text(): ", e)
            http_code = 500
            document = None
            message = str(e)
        logging.info('document: ' + str(document))
        return document, http_code, message
