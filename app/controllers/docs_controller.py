try:
    import logging
    import json
    import os
    from flask import Blueprint, jsonify, redirect, request, make_response, send_from_directory
    from flask_httpauth import HTTPBasicAuth

    from services.security import Security
    from services.cipher import Cipher
    from services.googledrive import DriverDocs
    from services.driverepo import DriverRepo
    from services.aws_s3 import Aws
    from services.api_docu import ApiDocs
    from services.adocsrepo import ADocsRepo

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[controllers] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

docs_bp = Blueprint('docs', __name__)
auth = HTTPBasicAuth()

SERVER_API_KEY = os.environ.get('SERVER_API_KEY', 'None')
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@auth.verify_password
def verify_password(username, password):
    if username is not None:
        basic_auth = Security()
        user = basic_auth.verifiy_user_pass(username, password)
        del basic_auth
        return user
    return None


@auth.error_handler
def unauthorized():
    return make_response(jsonify({'data': None, 'message': 'invalid credentials for basic auth'}), 401)


@docs_bp.route('/docs', methods=['GET', 'POST'])
def index():
    return redirect('/info'), 302


@docs_bp.route('/info', methods=['GET', 'POST'])
def info():
    return jsonify({
        "Servidor": "dev.jonnattan.com",
        "Nombre": "API de Documentos para distintos repos",
        "Support": "Drive"
    })


@docs_bp.route('/favicon.ico', methods=['POST', 'GET', 'PUT'])
def favicon():
    file_path = os.path.join(APP_DIR, 'static', 'image')
    logging.info("Icono: " + str(file_path))
    return send_from_directory(file_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@docs_bp.route('/docs/<path:subpath>', methods=['POST', 'GET'])
@auth.login_required
def process_all(subpath: str):
    logging.info(f"================== {request.method} /docs/{subpath} ==================")

    rx_api_key = request.headers.get('x-api-key')
    if rx_api_key is None or str(rx_api_key) != str(SERVER_API_KEY):
        logging.info("API Key invalida o no presente")
        return jsonify({'data': None, 'message': 'No autorizado'}), 401

    # Selección de servicio según prefijo de ruta
    service: ADocsRepo = None
    if subpath.startswith('drive/'):
        service = DriverDocs()
    elif subpath.startswith('v2/drive/'):
        service = DriverRepo()
    elif subpath.startswith('s3/'):
        service = Aws()
    elif subpath.startswith('api/'):
        service = ApiDocs()

    if service is None:
        logging.info('No se encontro implementacion para: ' + str(subpath))
        return jsonify({'data': None, 'message': 'No Found'}), 404

    # Parseo del cuerpo de la solicitud
    request_type = None
    data_rx = None
    json_data = None
    try:
        request_data = request.get_json()
        if request_data:
            request_type = request_data.get('type')
            data_rx = request_data.get('data')
    except Exception:
        pass

    # Desencriptación AES si el payload viene cifrado
    if data_rx is not None and str(request_type) == 'encrypted' and request.method == 'POST':
        cipher = Cipher()
        data_cipher = str(data_rx)
        logging.info('Data Encrypt: ' + str(data_cipher))
        data_clear = cipher.aes_decrypt(data_cipher)
        logging.info('Data EnClaro: ' + str(data_clear))
        json_data = json.dumps(data_clear)
    else:
        json_data = data_rx

    logging.info("JSON Data: " + str(json_data))

    # Despacho al método correspondiente del servicio
    path = subpath.lower().strip()
    if json_data is not None and path.find('/search') > -1 and request.method == 'POST':
        response, http_code = service.search(json_data)
    elif path.find('/list') > -1:
        response, http_code = service.list(json_data)
    else:
        response, http_code = service.process(path, json_data, str(request.method))

    logging.info('Procesado por ' + str(service))
    del service
    return jsonify(response), http_code
