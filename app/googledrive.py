#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import json
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
    cipher = None
    credential_file = None
    def __init__(self, root_dir : str = str(ROOT_DIR)) :
        try:
            self.root_dir = root_dir
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
            name_file = str(os.environ.get('GOOGLE_CREDENTIALS_JSON','None'))
            if name_file != "None":
                self.credential_file = root_dir + "/" + name_file
            self.cipher = Cipher()
        except Exception as e :
            print("ERROR :", e)
            self.root_dir = None
            self.api_key = None
            self.credential_file = None
            self.cipher = None

    def __del__(self):
        self.root_dir = None
        self.api_key = None
        del self.cipher
        self.cipher = None

    def login(self):
        credentials = None
        try:
            GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = self.credential_file
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile(self.credential_file)
            if gauth.credentials is None:
                logging.info("Create access token" )
                gauth.LocalWebserverAuth(port_numbers=[8092])
            elif gauth.access_token_expired:
                logging.info("Refresh token" )
                gauth.Refresh()
            else:
                logging.info("Auth Ok" )
                gauth.Authorize()
            gauth.SaveCredentialsFile(self.credential_file)
            credentials = GoogleDrive(gauth)
        except Exception as e :
           print("ERROR list_folder():", e)
        return credentials

    def list_folder (self, json_data ) :
        msg = 'Servicio ejecutado correctamente'
        code = 200
        files = []
        try:
            folder_id = json_data["folder_id"]
            drive = self.login()
            query = "'{}' in parents".format(folder_id)
            # logging.info('Query: ' + str(query))
            files_list = drive.ListFile({'q': query}).GetList()
            for f in files_list:
                files.append(f)
        except Exception as e :
           print("ERROR list_folder():", e)
           code = 500
           msg = str(e)
           files = []
        return msg, code, files

    def search_file (self, json_data ) :
        msg = 'Servicio ejecutado correctamente'
        code = 200
        files = []
        try:
            folder_id = json_data["folder_id"]
            file_name = json_data["file_name"]
            drive = self.login()
            query = "'{}' in parents".format(folder_id)
            files_list = drive.ListFile({'q': query}).GetList()
            for f in files_list:
                title = f['title']
                if( title.find(file_name) >= 0 ) :
                    files.append(f)
        except Exception as e :
           print("ERROR search_file():", e)
           code = 500
           msg = str(e)
           files = []
        return msg, code, files

    def read_file (self, json_data ) :
        msg = 'Servicio ejecutado correctamente'
        code = 200
        data_rx = None
        try:
            file_id = json_data["file_id"]
            drive = self.login()
            query = "'id':'{}'".format(str(file_id))
            logging.info('Query: ' + str(query))
            file = drive.CreateFile({'id': file_id}) 
            file_name = file['title']
            logging.info('File: ' + str(file))
            path_file = self.root_dir + "/static/" + file_name
            file.GetContentFile(path_file)
            
            links = None 
            try :
                if file['exportLinks'] != None :
                    links = file['exportLinks']
            except Exception as e :
                links = None 

            data_rx = {
              "link": file['embedLink'],
              "internal_route": path_file,
              "title": file['title'],
              "size_bytes": file['fileSize'],
              "created_date": file['createdDate'],
              "type": file['mimeType'],
              "other_links": links,
            }
        except Exception as e :
           print("ERROR read_file():", e)
           code = 500
           msg = str(e)
           path_file = None
        return msg, code, data_rx

    def request_process(self, request, subpath ) :
        message = "Servicio ejecutado exitosamente"
        http_code  = 200
        data_response = None
        response =  {"message" : message, "data": data_response}

        logging.info("Reciv " + str(request.method) + " Contex: /drive/" + str(subpath) )
        #logging.info("Reciv Header :\n" + str(request.headers) )
        #logging.info("Reciv Data: " + str(request.data) )
        rx_api_key = request.headers.get('x-api-key')
        if str(rx_api_key) != str(self.api_key) :
            response = {"message" : "No autorizado", "data": data_response }
            http_code  = 401
            return  response, http_code
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
        if request.method == 'POST' :
            if str(subpath).find('login') >= 0 :
                credentials = self.login()
                logging.info("Login :" + str(credentials) )
            if str(subpath).find('list') >= 0 :
               message, http_code, data_response = self.list_folder(json_data)
            if str(subpath).find('read') >= 0 :
               message, http_code, data_response = self.read_file(json_data)
            if str(subpath).find('search') >= 0 :
               message, http_code, data_response = self.search_file(json_data)
        
        response = {"data": data_response, "message" : message }
        return  response, http_code