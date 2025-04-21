#!/usr/bin/python

try:
    import logging
    import sys
    import os
    import time
    import requests
    import json
    from flask_cors import CORS
    from flask_wtf.csrf import CSRFProtect
    from flask_httpauth import HTTPBasicAuth
    from flask_login import LoginManager, UserMixin, current_user, login_required, login_user
    from flask import Flask, render_template, abort, make_response, request, redirect, jsonify, send_from_directory
    # Clases personales
    from security import Security
    from googledrive import DriverDocs
    from api_docu import ApiDocs

except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[http-server] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

############################# Configuraci'on de Registro de Log  ################################
FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
# Log en pantalla
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
#fh = logging.FileHandler('logger.log')
#fh.setLevel(logging.INFO)
#fh.setFormatter(formatter)
# se meten ambas configuraciones
root.addHandler(handler)
#root.addHandler(fh)

logger = logging.getLogger('HTTP')
# ===============================================================================
# Configuraciones generales del servidor Web
# ===============================================================================

app = Flask(__name__)

#login_manager = LoginManager()
#login_manager.init_app(app)

csrf = CSRFProtect()
csrf.init_app(app)

auth = HTTPBasicAuth()
cors = CORS(app, resources={r"/docs/*": {"origins": ["dev.jonnattan.com"]}})
# ===============================================================================
# variables globales
# ===============================================================================
ROOT_DIR = os.path.dirname(__file__)

#===============================================================================
# Redirige
#===============================================================================
@app.route('/docs', methods=['GET', 'POST'])
@csrf.exempt
def index():
    return redirect('/info'), 302
@app.route('/docs/<path:subpath>', methods=['POST', 'GET'])
@csrf.exempt
def other():
    return redirect('/info'), 302
#===============================================================================
# Informaci'on
#===============================================================================
@app.route('/info', methods=['GET', 'POST'])
@csrf.exempt
def info_proccess():
    return jsonify({
        "Servidor": "dev.jonnattan.com",
        "Nombre": "API de Documentos para distitos repos",
        "Support":"Drive"
    })
#===============================================================================
# Metodo solicitado por la biblioteca de autenticaci'on b'asica
#===============================================================================
@auth.verify_password
def verify_password(username, password):
    user = None
    if username != None :
        basicAuth = Security()
        user =  basicAuth.verifiyUserPass(username, password)
        del basicAuth
    return user

#==================================================================================
# Implementacion del handler que respondera el error en caso de mala autenticacion
#==================================================================================
@auth.error_handler
def unauthorized():
    return make_response(jsonify({'message':'invalid credentials'}), 401)

# ==============================================================================
# Procesa peticiones de la pagina de la logia
# ==============================================================================
@app.route('/docs/drive/<path:subpath>', methods=['POST', 'GET'])
@csrf.exempt
@auth.login_required
def process_drive(subpath):
    drive = DriverDocs( str(ROOT_DIR) )
    data_response, http_code = drive.request_process( request, subpath )
    del drive
    return jsonify(data_response), http_code

@app.route('/docs/api', methods=['POST', 'GET'])
@csrf.exempt
@auth.login_required
def process_api_only():
    api = ApiDocs()
    data_response, http_code = api.request_process( request, '' )
    del api
    return jsonify(data_response), http_code

@app.route('/docs/api/<path:subpath>', methods=['POST', 'GET'])
@csrf.exempt
@auth.login_required
def process_api(subpath):
    api = ApiDocs()
    data_response, http_code = api.request_process( request, subpath )
    del api
    return jsonify(data_response), http_code

# ===============================================================================
# Favicon
# ===============================================================================
@app.route('/favicon.ico', methods=['POST','GET','PUT'])
@csrf.exempt
def favicon():
    file_path = os.path.join(ROOT_DIR, 'static')
    file_path = os.path.join(file_path, 'image')
    logging.info("Icono: " + str( file_path ) )
    return send_from_directory(file_path,
            'favicon.ico', mimetype='image/vnd.microsoft.icon')

# ===============================================================================
# Metodo Principal que levanta el servidor
# ===============================================================================
if __name__ == "__main__":
    listenPort = 8085
    logger.info("ROOT_DIR: " + ROOT_DIR)
    logger.info("ROOT_DIR: " + app.root_path)
    if(len(sys.argv) == 1):
        logger.error("Se requiere el puerto como parametro")
        exit(0)
    try:
        logger.info("Server listen at: " + sys.argv[1])
        listenPort = int(sys.argv[1])
        # app.run(ssl_context='adhoc', host='0.0.0.0', port=listenPort, debug=True)
        # app.run( ssl_context=('cert_jonnattan.pem', 'key_jonnattan.pem'), host='0.0.0.0', port=listenPort, debug=True)
        app.run( host='0.0.0.0', port=listenPort)
    except Exception as e:
        print("ERROR MAIN:", e)

    logging.info("PROGRAM FINISH")
