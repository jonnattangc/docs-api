try:
    import logging
    import sys
    import os
    from Crypto.Cipher import AES
    import base64

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[Cipher] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


class Cipher():
    aes_key = None
    iv = None

    def __init__(self):
        key = os.environ.get('AES_KEY', 'None')
        self.aes_key = key.encode('utf-8')[:32]
        self.iv = b'1234567890123456'

    def __del__(self):
        self.aes_key = None
        self.iv = None

    def complete(self, data_str: str):
        response = data_str
        if data_str is not None:
            length = len(data_str)
            resto = 16 - (length % 16)
            for _ in range(resto):
                response += " "
        return response.encode()

    def aes_encrypt(self, payload: str):
        data_cipher_str = None
        try:
            data_clear = self.complete(payload)
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
            data_cipher = cipher.encrypt(data_clear)
            if data_cipher is not None:
                b64 = base64.b64encode(data_cipher)
                data_cipher_str = b64.decode()
        except Exception as e:
            print("ERROR Cipher:", e)
        return data_cipher_str

    def aes_decrypt(self, data_cipher_str: str):
        data_clear_str = None
        try:
            b64 = data_cipher_str.encode()
            data_cipher = base64.b64decode(b64)
            cipher = AES.new(self.aes_key, AES.MODE_CBC, self.iv)
            data_clear = cipher.decrypt(data_cipher)
            if data_clear is not None:
                data_clear_str = data_clear.decode()
                data_clear_str = data_clear_str.strip()
        except Exception as e:
            print("ERROR Decipher:", e)
        return data_clear_str
