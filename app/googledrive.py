#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import json
    from cipher import Cipher
    from flask import jsonify
    import base64
    import hashlib
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    from pydrive2.files import FileNotUploadedError

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


ROOT_DIR : str = str(os.path.dirname(__file__))

class DriverDocs () :
    root_dir = None
    api_key = None
    cipher = None
    credential_file : str = None
    docs_folder: str = None
    # Id de carpetas
    apr_folder_id: str = None
    mae_folder_id: str = None
    com_folder_id: str = None

    def __init__(self) :
        try:
            self.root_dir = ROOT_DIR
            self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
            self.credential_file = str(os.environ.get('GOOGLE_CREDENTIALS_JSON', None))
            if self.credential_file == None:
                raise Exception("GOOGLE_CREDENTIALS_JSON: " + str(self.credential_file) )
            logging.info("Credentials file: " + str(self.credential_file) )
            work_dir = str(os.environ.get('DOCS_WORK_DIR','None'))
            if work_dir != None :
                self.docs_folder = self.root_dir + work_dir
                logging.info("Docs work folder: " + str(self.docs_folder) )

            self.apr_folder_id = str(os.environ.get('APREDIZ_FOLDER','None'))
            self.com_folder_id = str(os.environ.get('COMPANERO_FOLDER','None'))
            self.mae_folder_id = str(os.environ.get('MAESTRO_FOLDER','None'))

            if self.apr_folder_id.find("None") >= 0 :
                raise Exception("APR folder id: " + str(self.apr_folder_id) )
            if self.com_folder_id.find("None") >= 0 :
                raise Exception("COMP folder id: " + str(self.com_folder_id) )
            if self.mae_folder_id.find("None") >= 0 :
                raise Exception("MESTER folder id: " + str(self.mae_folder_id) )

            self.cipher = Cipher()
        except Exception as e :
            print("ERROR __init__ :", e)
            self.root_dir = None
            self.api_key = None
            self.credential_file = None
            if self.cipher != None :
                del self.cipher
                self.cipher = None

    def __del__(self):
        self.root_dir = None
        self.api_key = None
        if self.cipher != None :
            del self.cipher
        self.cipher = None

    def login(self):
        credentials = None
        http_code  = 200
        message = None
        try:
            if os.path.exists(self.credential_file):
                # os.chmod(self.credential_file, 0o755)
                logging.info("Credentials file exist: " + str(self.credential_file) )
            else:
                raise Exception("Credentials file not exist: " + str(self.credential_file) )
            GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = self.credential_file
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile(self.credential_file)
            if gauth.credentials is None:
                logging.info("Create access token" )
                resp = gauth.LocalWebserverAuth()
                logging.info("Access token created Ok..." )
            elif gauth.access_token_expired:
                logging.info("Refresh token" )
                gauth.Refresh()
                logging.info("token refreshed Ok..." )
            else:
                logging.info("Auth Ok" )
                gauth.Authorize()
                message = "Authentication Ok..."
            gauth.SaveCredentialsFile(self.credential_file)
            credentials = GoogleDrive(gauth)
        except Exception as e :
           print("ERROR login(): ", e)
           http_code  = 401
           message = str(e)        
        return credentials, http_code, message

    def get_grade_to_folder (self, folder_name: str ) :
        folder_id : str = self.apr_folder_id
        fn = folder_name.lower().replace("/", "").replace(" ", "").replace("\t", "").replace("\n", "")
        if fn == 'aprendiz' or fn == 'primero' or fn == '1' :
            folder_id = self.apr_folder_id
        elif fn == 'compañero' or fn == 'segundo' or fn == '2' :
            folder_id = self.com_folder_id
        elif fn == 'maestro' or fn == 'tercero' or fn == '3' :
            folder_id = self.mae_folder_id
        else :
            folder_id = self.apr_folder_id
        return folder_id

    def get_folder_to_grade (self, folder_id: str ) :
        grade : str = '-'

        if folder_id == self.apr_folder_id :
            grade = '1'
        elif folder_id == self.com_folder_id :
            grade = '2'
        elif folder_id == self.mae_folder_id :
            grade = '3'
        else :
            grade = '-'
        return grade

    def list_files (self, json_data ) :
        msg = 'Servicio ejecutado correctamente'
        code = 200
        files = []
        try:
            #folder_query = '("{}" in parents or "{}" in parents or "{}" in parents)'.format(self.apr_folder_id, self.mae_folder_id, self.com_folder_id)
            folder_query = '('
            folders = json_data["folders"]
            if folders != None and len(folders) > 0 :
                count = 0
                for fld in folders :
                    folder_id = self.get_grade_to_folder(str(fld))
                    if count > 0 :
                        folder_query += ' or '
                    folder_query += "'{}' in parents".format(folder_id)
                    count += 1
                folder_query += ') and trashed=false'
                logging.info('Folders query: ' + str(folder_query))
            else :
                msg = 'Error en la consulta de carpetas'
                code = 500
                return msg, code, files

            query = folder_query
            filters = []
            try :
                filters = json_data["filters"]
            except Exception as e :
                filters = []
            if filters != None and len(filters) > 0 :
                for f in filters :
                    query += " and {} {} '{}'".format(str(f["filter_name"]), str(f["comparation"]), str(f["filter_value"]))
                logging.info('Query whit Filters: ' + str(query))
            
            drive, code, error_msg = self.login()
            if code != 200 :
                return error_msg, code, files

            files_response = drive.ListFile({'q': query}).GetList()
            for f in files_response:
                f['grade_folder'] = self.get_folder_to_grade(str(f['parents'][0]['id']))
                files.append(f)

            logging.info('Response ' + str(len(files)) + ' elementos: ')

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
            drive, code, error_msg = self.login()
            if code != 200 :
                return error_msg, code, files
            
            folder_id : str = json_data["folder_id"]
            query = "'{}' in parents".format(folder_id)
            
            filters = []
            try :
                filters = json_data["filters"]
            except Exception as e :
                filters = []
            if filters != None and len(filters) > 0 :
                for f in filters :
                    query += " and {} {} '{}'".format(str(f["filter_name"]), str(f["comparation"]), str(f["filter_value"]))
                logging.info('Query whit Filters: ' + str(query))
            
            files_list = drive.ListFile({'q': query}).GetList()

            only_id : bool = False
            try :
                only_id = json_data["only_id"]
            except Exception as e :
                only_id = False

            for f in files_list:
                title = f['title']
                if only_id :
                    files.append({"id": f['id']})
                else :
                    files.append(f)
                break
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
            folder_id : str = self.get_grade_to_folder(str(json_data["folder"]))
            file_name :str = json_data["name_file"]
            logging.info("Folder ID: " + str(folder_id) + ', File Name: ' + str(file_name) + ', MD5: ' + str(json_data["md5sum"]) )
            json_data["folder_id"] = folder_id
            
            file_id, code, data_files = self.search_file(json_data)
            if code != 200 :
                return msg, code, data_files

            logging.info("FILES: " + str(data_files) )

            file_id = data_files[0]["id"]
            logging.info("FILE ID: " + str(file_id) )

            drive, code, error_msg = self.login()
            if code != 200 :
                return error_msg, code, data_rx

            file = drive.CreateFile({'id': file_id}) 
            drive_file_title :str = file['title']
            
            path_file : str = None
            file_b64 : str = None
            md5_calculated : str = None

            require_detail : bool = False
            try :
                require_detail = json_data["require_detail"]
            except Exception as e :
                require_detail = False

            doc_required : bool = False
            try :
                doc_required = json_data["require_base64_file"]
            except Exception as e :
                doc_required = False
            
            if doc_required : 
                path_file = self.docs_folder + file_name
                logging.info("###### path_file: " + str(path_file) )
                file.GetContentFile(path_file)
                file_bytes = None
                with open(path_file, "rb") as pdf_file:
                    flbytes = pdf_file.read()
                    md5_calculated = self.calculate_md5(flbytes)
                    file_bytes = base64.b64encode(flbytes)
                if file_bytes != None :
                    file_b64 = file_bytes.decode('utf-8')
                
            if require_detail :
                links = None 
                try :
                    if file['exportLinks'] != None :
                        links = file['exportLinks']
                except Exception as e :
                    links = None 

                data_rx = {
                    "link": file['embedLink'],
                    "internal_route": path_file,
                    "file_b64": file_b64,
                    "md5": md5_calculated,
                    "title": file_name,
                    "size_bytes": file['fileSize'],
                    "created_date": file['createdDate'],
                    "type": file['mimeType'],
                    "other_links": links,
                }
            else :
                data_rx = {
                    "title": drive_file_title,
                    "md5": md5_calculated,
                    "size_bytes": file['fileSize'],
                    "type": file['mimeType'],
                    "file_b64": file_b64,
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
        json_data = None
        logging.info("Reciv " + str(request.method) + " Contex: /docs/drive/" + str(subpath) )
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
                credentials, http_code, message = self.login()
                message = str(credentials.GetAbout()['name']) + ' ' + str(message)
                logging.info("Login Name: " + str(credentials.GetAbout()['name']) + ' language: ' + str(credentials.GetAbout()['languageCode']) )
            if str(subpath).find('list') >= 0 :
               message, http_code, data_response = self.list_files(json_data)
            if str(subpath).find('read') >= 0 :
               message, http_code, data_response = self.read_file(json_data)
            if str(subpath).find('search') >= 0 :
               message, http_code, data_response = self.search_file(json_data)
        elif request.method == 'GET' :
            if str(subpath).find('read') >= 0 :
               message, http_code, data_response = self.read_file(json_data)

        response = {"data": data_response, "message" : message }
        return  response, http_code

    
    def calculate_md5(self, data_bytes):
        if data_bytes is None:
            return None
        md5_hash = hashlib.md5()
        md5_hash.update(data_bytes)
        return md5_hash.hexdigest()