#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import base64
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
    from .adocsrepo import ADocsRepo

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

# Apunta al directorio app/, un nivel arriba de services/
APP_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DriverDocs(ADocsRepo):
    root_dir = None
    credential_file: str = None
    docs_folder: str = None
    apr_folder_id: str = None
    mae_folder_id: str = None
    com_folder_id: str = None

    def __init__(self):
        super().__init__()
        try:
            self.root_dir = APP_DIR
            self.credential_file = str(os.environ.get('GOOGLE_CREDENTIALS_JSON', None))
            if self.credential_file is None:
                raise Exception("GOOGLE_CREDENTIALS_JSON: " + str(self.credential_file))
            logging.info("Credentials file: " + str(self.credential_file))
            work_dir = str(os.environ.get('DOCS_WORK_DIR', 'None'))
            if work_dir is not None:
                self.docs_folder = self.root_dir + work_dir
                logging.info("Docs work folder: " + str(self.docs_folder))

            self.apr_folder_id = str(os.environ.get('APREDIZ_FOLDER', 'None'))
            self.com_folder_id = str(os.environ.get('COMPANERO_FOLDER', 'None'))
            self.mae_folder_id = str(os.environ.get('MAESTRO_FOLDER', 'None'))

            if self.apr_folder_id.find("None") >= 0:
                raise Exception("APR folder id: " + str(self.apr_folder_id))
            if self.com_folder_id.find("None") >= 0:
                raise Exception("COMP folder id: " + str(self.com_folder_id))
            if self.mae_folder_id.find("None") >= 0:
                raise Exception("MESTER folder id: " + str(self.mae_folder_id))

        except Exception as e:
            print("ERROR __init__ :", e)
            self.root_dir = None
            self.credential_file = None

    def __del__(self):
        self.root_dir = None

    def login(self):
        credentials = None
        http_code = 200
        message = None
        try:
            logging.info("Credentials file exist verify: " + str(self.credential_file))
            if os.path.exists(self.credential_file):
                logging.info("Credentials file exist: " + str(self.credential_file))
            else:
                raise Exception("Credentials file not exist: " + str(self.credential_file))
            GoogleAuth.DEFAULT_SETTINGS['client_config_file'] = self.credential_file
            gauth = GoogleAuth()
            gauth.LoadCredentialsFile(self.credential_file)
            if gauth.credentials is None:
                resp = gauth.LocalWebserverAuth()
                gauth.SaveCredentialsFile(self.credential_file)
            elif gauth.access_token_expired:
                gauth.Refresh()
                gauth.SaveCredentialsFile(self.credential_file)
            else:
                gauth.Authorize()
                message = "Authentication Ok..."
            credentials = GoogleDrive(gauth)
        except Exception as e:
            print("ERROR login(): ", e)
            http_code = 401
            message = str(e)
        return credentials, http_code, message

    def get_grade_to_folder(self, folder_name: str):
        fn = folder_name.lower().replace("/", "").replace(" ", "").replace("\t", "").replace("\n", "")
        if fn == 'aprendiz' or fn == 'primero' or fn == '1':
            return self.apr_folder_id
        elif fn == 'compañero' or fn == 'segundo' or fn == '2':
            return self.com_folder_id
        elif fn == 'maestro' or fn == 'tercero' or fn == '3':
            return self.mae_folder_id
        return self.apr_folder_id

    def get_folder_to_grade(self, folder_id: str):
        if folder_id == self.apr_folder_id:
            return '1'
        elif folder_id == self.com_folder_id:
            return '2'
        elif folder_id == self.mae_folder_id:
            return '3'
        return '-'

    def list(self, json_data) -> tuple:
        msg = 'Servicio ejecutado correctamente'
        code = 200
        files = []
        try:
            logging.info('json_data: ' + str(json_data))
            folder_query = '('
            folders = json_data["folders"]
            if folders is not None and len(folders) > 0:
                count = 0
                for fld in folders:
                    folder_id = self.get_grade_to_folder(str(fld))
                    if count > 0:
                        folder_query += ' or '
                    folder_query += "'{}' in parents".format(folder_id)
                    count += 1
                folder_query += ') and trashed=false'
                logging.info('Folders query: ' + str(folder_query))
            else:
                return {'data': None, 'message': 'Error en la consulta de carpetas'}, 500

            query = folder_query
            filters = []
            try:
                filters = json_data["filters"]
            except Exception:
                filters = []
            if filters is not None and len(filters) > 0:
                for f in filters:
                    query += " and {} {} '{}'".format(str(f["filter_name"]), str(f["comparation"]), str(f["filter_value"]))
                logging.info('Query whit Filters: ' + str(query))

            drive, code, error_msg = self.login()
            if code != 200:
                return {'data': None, 'message': error_msg}, code

            files_response = drive.ListFile({'q': query}).GetList()
            for f in files_response:
                f['grade_folder'] = self.get_folder_to_grade(str(f['parents'][0]['id']))
                files.append(f)

            logging.info('Response ' + str(len(files)) + ' elementos: ')

        except Exception as e:
            print("ERROR list_folder():", e)
            code = 500
            msg = str(e)
            files = []
        return {'data': files, 'message': msg}, code

    def search(self, json_data) -> tuple:
        msg = 'Servicio ejecutado correctamente'
        code = 200
        files = []
        try:
            drive, code, error_msg = self.login()
            if code != 200:
                return {'data': None, 'message': error_msg}, code

            folder_id: str = json_data["folder_id"]
            query = "'{}' in parents".format(folder_id)

            filters = []
            try:
                filters = json_data["filters"]
            except Exception:
                filters = []
            if filters is not None and len(filters) > 0:
                for f in filters:
                    query += " and {} {} '{}'".format(str(f["filter_name"]), str(f["comparation"]), str(f["filter_value"]))
                logging.info('Query whit Filters: ' + str(query))

            files_list = drive.ListFile({'q': query}).GetList()

            only_id: bool = False
            try:
                only_id = json_data["only_id"]
            except Exception:
                only_id = False

            for f in files_list:
                if only_id:
                    files.append({"id": f['id']})
                else:
                    files.append(f)
                break
        except Exception as e:
            print("ERROR search_file():", e)
            code = 500
            msg = str(e)
            files = []

        return {'data': files, 'message': msg}, code

    def read_file(self, json_data):
        msg = 'Servicio ejecutado correctamente'
        code = 200
        data_rx = None
        try:
            folder_id: str = self.get_grade_to_folder(str(json_data["folder"]))
            file_name: str = json_data["name_file"]
            logging.info("Folder ID: " + str(folder_id) + ', File Name: ' + str(file_name) + ', MD5: ' + str(json_data["md5sum"]))
            json_data["folder_id"] = folder_id

            file_id, code, data_files = self.search_file(json_data)
            if code != 200:
                return msg, code, data_files

            logging.info("FILES: " + str(data_files))
            file_id = data_files[0]["id"]
            logging.info("FILE ID: " + str(file_id))

            drive, code, error_msg = self.login()
            if code != 200:
                return error_msg, code, data_rx

            file = drive.CreateFile({'id': file_id})
            drive_file_title: str = file['title']

            path_file: str = None
            file_b64: str = None
            md5_calculated: str = None

            require_detail: bool = False
            try:
                require_detail = json_data["require_detail"]
            except Exception:
                require_detail = False

            doc_required: bool = False
            try:
                doc_required = json_data["require_base64_file"]
            except Exception:
                doc_required = False

            if doc_required:
                path_file = self.docs_folder + file_name
                logging.info("###### path_file: " + str(path_file))
                file.GetContentFile(path_file)
                with open(path_file, "rb") as pdf_file:
                    flbytes = pdf_file.read()
                    md5_calculated = self.calculate_md5(flbytes)
                    file_bytes = base64.b64encode(flbytes)
                if file_bytes is not None:
                    file_b64 = file_bytes.decode('utf-8')

            if require_detail:
                links = None
                try:
                    if file['exportLinks'] is not None:
                        links = file['exportLinks']
                except Exception:
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
            else:
                data_rx = {
                    "title": drive_file_title,
                    "md5": md5_calculated,
                    "size_bytes": file['fileSize'],
                    "type": file['mimeType'],
                    "file_b64": file_b64,
                }

        except Exception as e:
            print("ERROR read_file():", e)
            code = 500
            msg = str(e)
        return msg, code, data_rx

    def process(self, subpath: str, json_data, method: str) -> tuple:
        message = "Servicio ejecutado exitosamente"
        http_code = 200
        data_response = None

        if method == 'POST':
            if str(subpath).find('login') >= 0:
                credentials, http_code, message = self.login()
                message = str(credentials.GetAbout()['name']) + ' ' + str(message)
                logging.info("Login Name: " + str(credentials.GetAbout()['name']))
            if str(subpath).find('read') >= 0:
                message, http_code, data_response = self.read_file(json_data)
        elif method == 'GET':
            if str(subpath).find('read') >= 0:
                message, http_code, data_response = self.read_file(json_data)

        return {'data': data_response, 'message': message}, http_code

    def get_implementation_name(self) -> str:
        return "GoogleDrive(v1.0.0)"
