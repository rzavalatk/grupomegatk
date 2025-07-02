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
    codigo = fields.Char("Codigo")
    user = fields.Char("Usuario")
    password = fields.Char("Password")
    token = fields.Char("Token de usuario")
    
    def limpiar_json_anviz(self, raw_data):
        # Eliminar coma extra antes de cerrar un objeto `}, }`
        limpio = re.sub(r'],\s*}', ']}', raw_data)
        return limpio
    
#http://192.168.10.34/goform/searchrecord?token=eyJhbGciOiJTSEExIiwidHlwIjoiSldUIn0=.eyJleHAiOiI5MDI4Nzg2NyIsImlhdCI6IjIwMjUtMDYtMTIgMTE6MDc6MDMiLCJpc3MiOiJFUDMwMFBSTy0wNzMwMjAwMDIzMzkwMDI3IiwianRpIjoiMiIsIm5iZiI6IjIwMjUtMDYtMTIgMTE6MDc6MDMiLCJwd24iOiIxMTUyOTIxNTA0NjA2ODQ2OTc1IiwidWlkIjoiYWRtaW4ifQ==.CM/rycAZQONciAE0/D+9fpGLyOY=&limit=2&from=2025-06-10&to=2025-06-10
    def obtener_token(self):
        try:
            url = f"http://{self.dir_ip}/anviz/login"
            params = {"userid": self.user, "password": self.password}
            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            raw = response.text
            _loggin.warning("Response.text: %s", raw)

            json_limpio = self.limpiar_json_anviz(raw)
            _loggin.warning("JSON limpio: %s", json_limpio)

            data = json.loads(json_limpio)

            # Si todavía es string, hacer segunda capa de decodificación
            if isinstance(data, str):
                _loggin.warning("Primera capa JSON todavía es str, aplicando segunda capa")
                data = json.loads(data)

            _loggin.warning("DATA FINAL: %s", data)
            _loggin.warning("Tipo de data: %s", type(data))

            if isinstance(data, dict) and data.get("code") == "success":
                self.token = data.get("token")
                return data
            else:
                raise Warning(f"Login fallido: {data.get('msg', 'Respuesta inesperada')}")

        except Exception as e:
            raise Warning(f"Error al conectarse con Anviz: {str(e)}")
