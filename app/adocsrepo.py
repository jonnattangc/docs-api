try:
    import logging
    import sys
    import os
    import json
    from cipher import Cipher
    from abc import ABC, abstractmethod
    import hashlib

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Cipher] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)

ROOT_DIR = os.path.dirname(__file__)

class ADocsRepo(ABC):

    api_key : str = None
    cipher : Cipher= None

    def __init__(self, ) -> None:
        self.api_key = str(os.environ.get('SERVER_API_KEY','None'))
        self.cipher = Cipher()

    def __del__(self):
        self.api_key = None
        if self.cipher != None :
            del self.cipher
        self.cipher = None

    @abstractmethod
    def process(self, subpath: str, json_data: str, method: str)  -> {dict, int} :
        pass
    
    @abstractmethod
    def search(self, json_data: str)  -> {dict, int} :
        pass

    @abstractmethod
    def list(self, json_data: str)  -> {dict, int} :
        pass

    def evaluate_request(self, request, subpath: str)  -> {dict, int} :
        request_type = None
        data_rx = None
        json_data: str = None
        http_code  = 401
        request_data = None
        response =  {"message" : 'No autorizado', "data": None}
        logging.info("Reciv " + str(request.method) + " Contex: /docs/" + str(subpath) )
        # logging.info("Reciv Header :\n" + str(request.headers) )
        # logging.info("Reciv Data: " + str(request.data) )

        path : str = '' 
        if subpath != None : 
            path = subpath.lower().strip()

        rx_api_key = request.headers.get('x-api-key')
        if rx_api_key == None :
            logging.info("No Header 'x-api-key'")
            return  response, http_code
        if str(rx_api_key) != str(self.api_key) :
            logging.error(f"API Key: {rx_api_key} != {self.api_key}" )
            return response, http_code
        try :
            request_data = request.get_json()
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
        
        logging.info("JSON Data: " + str(json_data) )

        if json_data != None and str(path).find('/search') > -1 and request.method == 'POST' :
            return self.search( json_data )
        
        if str(path).find('/list') > -1 :
            return self.list( json_data )

        return self.process( path, json_data, str(request.method) )


    @abstractmethod
    def get_implementation_name(self) -> str:
        pass 

    def __str__(self):
        return f"'{self.get_implementation_name()}' "

    def calculate_md5(self, data_bytes):
        if data_bytes is None:
            return None
        md5_hash = hashlib.md5()
        md5_hash.update(data_bytes)
        return md5_hash.hexdigest()