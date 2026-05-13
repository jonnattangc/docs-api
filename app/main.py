#!/usr/bin/python

try:
    import logging
    import sys
    import os
    from flask import Flask
    from flask_cors import CORS
    from flask_wtf.csrf import CSRFProtect
    from controllers.docs_controller import docs_bp

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[http-server] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

FORMAT = '%(asctime)s %(levelname)s : %(message)s'
root = logging.getLogger()
root.setLevel(logging.INFO)
formatter = logging.Formatter(FORMAT)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
handler.setFormatter(formatter)
root.addHandler(handler)

logger = logging.getLogger('HTTP')

app = Flask(__name__)

csrf = CSRFProtect()
csrf.init_app(app)

CORS(app, resources={r"/docs/*": {"origins": ["*.jonnattan.com", "*.jonna.cl", "*.jonnattan.cl", "logia.buenaventuracadiz.cl"]}})

csrf.exempt(docs_bp)
app.register_blueprint(docs_bp)

if __name__ == "__main__":
    listenPort = 8085
    logger.info("ROOT_DIR: " + app.root_path)
    if len(sys.argv) == 1:
        logger.error("Se requiere el puerto como parametro")
        exit(0)
    try:
        logger.info("Server listen at: " + sys.argv[1])
        listenPort = int(sys.argv[1])
        app.run(host='0.0.0.0', port=listenPort)
    except Exception as e:
        print("ERROR MAIN:", e)

    logging.info("PROGRAM FINISH")
