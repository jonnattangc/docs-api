#!/usr/bin/python

try:
    import logging
    import sys
    import os
    from cipher import Cipher
    from flask import jsonify
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    from pydrive2.files import FileNotUploadedError

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


ROOT_DIR = os.path.dirname(__file__)

class DriverDocs () :
    root_dir = None
    api_key = None
    def __init__(self, root_dir : str = str(ROOT_DIR)) :
        try:
            self.root_dir = root_dir
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
        except Exception as e :
            print("ERROR :", e)
            self.root_dir = None
            self.api_key = None

    def __del__(self):
        self.root_dir = None
        self.api_key = None

    def login():
        GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = directorio_credenciales
        gauth = GoogleAuth()
        gauth.LoadCredentialsFile(directorio_credenciales)
    
        if gauth.credentials is None:
            gauth.LocalWebserverAuth(port_numbers=[8091])
        elif gauth.access_token_expired:
            gauth.Refresh()
        else:
            gauth.Authorize()
        
        gauth.SaveCredentialsFile(directorio_credenciales)
        credenciales = GoogleDrive(gauth)
        return credenciales

    def request_process(self, request, subpath ) :
        message = "No autorizado"
        data_response = {"message" : message}
        http_code  = 401
        logging.info("Reciv " + str(request.method) + " Contex: /scraper/" + str(subpath) )
        logging.info("Reciv Header :\n" + str(request.headers) )
        logging.info("Reciv Data: " + str(request.data) )

        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()

        rx_api_key = request.headers.get('x-api-key')
        if str(rx_api_key) != str(self.api_key) :
            return  jsonify(data_response), http_code
        request_data = request.get_json()

        cipher = Cipher()
        response_data, http_code = cipher.test( request )
        # credentials = self.login()
        return  jsonify(data_response), http_code