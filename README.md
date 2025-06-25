# Api de documentos 
API para rescatar documentos de distintas fuentes, actualmente se prueba con 3
- Google Drive
- Aws S3 
- Servidor personal
- Proximamente DropBox

## AWS S3 
Para esto requiere que se tenba un usuario con permiso al bucket S3 que se pone en un archivo de configuración

## Drive
Se requiere crear una aplicación y configurarla para dar permisos a drive. El drive puede ser compartido con otras personas de manera que los documentos sean simplemente pegados allí.
Para hacer el permiso inicial se utiliza el programa sencillo llamado __drive.py__ que tiene como particularidad abrir una interfaz web de los permisos. Al dar estos permisos se crea el archivo de credenicales.
Con el archivo de credenciales se crea el setting.json y el client_secret  con los que finalmente se ejecuta la aplicación.