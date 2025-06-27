from odoo import models, fields, api
import subprocess
import json
import logging
import requests
import re

_loggin = logging.getLogger(__name__)

class ConexionAnviz(models.Model):
    _name = "conexion.anviz"
    _description = "Conexión a web service anviz desde Odoo"

    resultado = fields.Text("Resultado de la consulta")
    nombre = fields.Char("Nombre del dispositivo / regiòn")
    dir_ip = fields.Char("Direccion IP del dispositivo")
    region = fields.Char("Region")
    user = fields.Char("Usuario")
    password = fields.Char("Password")
    token = fields.Char("Token de usuario")
    
    def limpiar_json_anviz(raw_data):
        # Eliminar coma extra antes de cerrar un objeto `}, }`
        limpio = re.sub(r'],\s*}', ']}', raw_data)
        return limpio
    
#http://192.168.10.34/goform/searchrecord?token=eyJhbGciOiJTSEExIiwidHlwIjoiSldUIn0=.eyJleHAiOiI5MDI4Nzg2NyIsImlhdCI6IjIwMjUtMDYtMTIgMTE6MDc6MDMiLCJpc3MiOiJFUDMwMFBSTy0wNzMwMjAwMDIzMzkwMDI3IiwianRpIjoiMiIsIm5iZiI6IjIwMjUtMDYtMTIgMTE6MDc6MDMiLCJwd24iOiIxMTUyOTIxNTA0NjA2ODQ2OTc1IiwidWlkIjoiYWRtaW4ifQ==.CM/rycAZQONciAE0/D+9fpGLyOY=&limit=2&from=2025-06-10&to=2025-06-10
    def obtener_token(self):
        #Se obtendra el token desde una peticion http a la api de anviz
        #http://<IP>/goform/chklogin?userid=...&password=...

        if not self.dir_ip:
            raise Warning("No se ha ingresado la direccion IP")
        if not self.user:
            raise Warning("No se ha ingresado el usuario")
        if not self.password:
            raise Warning("No se ha ingresado el password")
        
        url = f"http://{self.dir_ip}/anviz/login"
        
        params = {
            'userid': self.user,
            'password': self.password
        }
        _loggin.warning(url)
        _loggin.warning(params)
        try:
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()
            data = json.loads(response)
            
            _loggin.warning(data)
            self.token = data
            """if data.get("code") == "success":
                _loggin.warning(data)
                self.token = data
                return data
            else:
                raise Warning(f"Login fallido: {data.get('msg')}")"""
        except Exception as e:
            raise Warning(f"Error al conectarse con Anviz: {str(e)}")
    