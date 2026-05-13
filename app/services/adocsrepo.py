try:
    import logging
    import sys
    import os
    import hashlib
    from abc import ABC, abstractmethod

except ImportError:
    logging.error(ImportError)
    print((os.linesep * 2).join(['[ADocsRepo] Error al buscar los modulos:', str(sys.exc_info()[1]), 'Debes Instalarlos para continuar', 'Deteniendo...']))
    sys.exit(-2)


class ADocsRepo(ABC):

    def __init__(self) -> None:
        pass

    @abstractmethod
    def process(self, subpath: str, json_data, method: str) -> tuple:
        pass

    @abstractmethod
    def search(self, json_data) -> tuple:
        pass

    @abstractmethod
    def list(self, json_data) -> tuple:
        pass

    @abstractmethod
    def get_implementation_name(self) -> str:
        pass

    def __str__(self):
        return f"'{self.get_implementation_name()}'"

    def calculate_md5(self, data_bytes):
        if data_bytes is None:
            return None
        md5_hash = hashlib.md5()
        md5_hash.update(data_bytes)
        return md5_hash.hexdigest()
