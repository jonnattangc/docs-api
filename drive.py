#!/usr/bin/python

try:
    import logging
    import sys
    import os
    from pydrive2.auth import GoogleAuth
except ImportError:

    logging.error(ImportError)
    print((os.linesep * 2).join(['[DriverDocs] Error al buscar los modulos:',
                                 str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


gauth = GoogleAuth()
gauth.LocalWebserverAuth()