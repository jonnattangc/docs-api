#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import base64
    import io

    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    import googleapiclient.http

    from .adocsrepo import ADocsRepo

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverRepo] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

# Apunta al directorio app/, un nivel arriba de services/
APP_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class DriverRepo(ADocsRepo):
    docs_folder: str = None
    apr_folder_id: str = None
    mae_folder_id: str = None
    com_folder_id: str = None
    service = None

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self):
        super().__init__()
        try:
            service_account_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_file is None:
                raise Exception("Variable GOOGLE_SERVICE_ACCOUNT_JSON no definida")
            if not os.path.exists(service_account_file):
                raise Exception(f"Archivo no encontrado: {service_account_file}")
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=self.SCOPES
            )
            self.service = build('drive', 'v3', credentials=credentials, cache_discovery=False)

            work_dir = str(os.environ.get('DOCS_WORK_DIR', 'None'))
            if work_dir is not None:
                self.docs_folder = APP_DIR + work_dir
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

            logging.info("APR folder id: " + str(self.apr_folder_id))
            logging.info("COMP folder id: " + str(self.com_folder_id))
            logging.info("MAE folder id: " + str(self.mae_folder_id))

        except Exception as e:
            print("ERROR __init__ :", e)

    def login(self):
        http_code = 200
        message = None
        try:
            if self.service is None:
                service_account_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
                if service_account_file is None:
                    raise Exception("Variable GOOGLE_SERVICE_ACCOUNT_JSON no definida")
                if not os.path.exists(service_account_file):
                    raise Exception(f"Archivo no encontrado: {service_account_file}")
                logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_file, scopes=self.SCOPES
                )
                self.service = build('drive', 'v3', credentials=credentials, cache_discovery=False)
            logging.info("Service Account Auth OK")
        except Exception as e:
            print("ERROR login(): ", e)
            http_code = 401
            message = str(e)
        return self.service, http_code, message

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

            service, code, error_msg = self.login()
            if code != 200:
                return {'data': None, 'message': error_msg}, code

            results = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, md5Checksum, createdTime, modifiedTime, parents, webContentLink, webViewLink, owners(displayName, emailAddress), lastModifyingUser(displayName), description, sharedWithMeTime)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute()

            files = results.get('files', [])
            for f in files:
                if 'parents' in f and len(f['parents']) > 0:
                    f['grade_folder'] = self.get_folder_to_grade(str(f['parents'][0]))

            logging.info('Response ' + str(len(files)) + ' elementos')

        except Exception as e:
            print("ERROR list_folder():", e)
            code = 500
            msg = str(e)
            files = []
        return {'data': files, 'message': msg}, code

    def search_file(self, json_data):
        msg = 'Servicio ejecutado correctamente'
        code = 200
        files = []
        try:
            service, code, error_msg = self.login()
            if code != 200:
                return error_msg, code, files

            folder_id: str = json_data["folder_id"]
            query = "'{}' in parents and trashed=false".format(folder_id)

            filters = []
            try:
                filters = json_data["filters"]
            except Exception:
                filters = []
            if filters is not None and len(filters) > 0:
                for f in filters:
                    query += " and {} {} '{}'".format(str(f["filter_name"]), str(f["comparation"]), str(f["filter_value"]))
                logging.info('Query with Filters: ' + str(query))

            only_id: bool = False
            try:
                only_id = json_data["only_id"]
            except Exception:
                only_id = False

            files_list = service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name, mimeType, size, createdTime, parents)',
                supportsAllDrives=True,
                includeItemsFromAllDrives=True
            ).execute().get('files', [])

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
        return msg, code, files

    def search(self, json_data) -> tuple:
        msg, code, files = self.search_file(json_data)
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

            msg, code, data_files = self.search_file(json_data)
            if code != 200:
                return msg, code, data_files

            logging.info("FILES: " + str(data_files))
            file_id = data_files[0]["id"]
            logging.info("FILE ID: " + str(file_id))

            drive, code, error_msg = self.login()
            if code != 200:
                return error_msg, code, data_rx

            file_meta = drive.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, webViewLink, exportLinks',
                supportsAllDrives=True
            ).execute()

            drive_file_name: str = file_meta.get('name')

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
                request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
                fh = io.BytesIO()
                downloader = googleapiclient.http.MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                flbytes = fh.getvalue()
                with open(path_file, "wb") as pdf_file:
                    pdf_file.write(flbytes)
                md5_calculated = self.calculate_md5(flbytes)
                file_bytes = base64.b64encode(flbytes)
                if file_bytes is not None:
                    file_b64 = file_bytes.decode('utf-8')
                # se elimina el archivo temporal para no generar problemas de espacio en POD
                try:
                    if os.path.exists(path_file):
                        os.remove(path_file)
                except Exception as e:
                    logging.error(f"Error al intentar borrar: {str(e)}")
                    
            if require_detail:
                data_rx = {
                    "link": file_meta.get('webViewLink'),
                    "internal_route": path_file,
                    "file_b64": file_b64,
                    "md5": md5_calculated,
                    "title": file_name,
                    "size_bytes": file_meta.get('size'),
                    "created_date": file_meta.get('createdTime'),
                    "type": file_meta.get('mimeType'),
                    "other_links": file_meta.get('exportLinks'),
                }
            else:
                data_rx = {
                    "title": drive_file_name,
                    "md5": md5_calculated,
                    "size_bytes": file_meta.get('size'),
                    "type": file_meta.get('mimeType'),
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
            if str(subpath).find('list') >= 0:
                return self.list(json_data)
            if str(subpath).find('read') >= 0:
                message, http_code, data_response = self.read_file(json_data)
            if str(subpath).find('search') >= 0:
                return self.search(json_data)
        elif method == 'GET':
            if str(subpath).find('read') >= 0:
                message, http_code, data_response = self.read_file(json_data)

        return {'data': data_response, 'message': message}, http_code

    def get_implementation_name(self) -> str:
        return "GoogleDrive(v2.0.0)"
