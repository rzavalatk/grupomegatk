from odoo import models, fields, api
import subprocess
import json

class ConexionSQLServer(models.Model):
    _name = "conexion.sqlserver"
    _description = "Conexión a SQL Server desde Odoo"

    resultado = fields.Text("Resultado de la consulta")

    #@api.model
    def obtener_datos_desde_sql(self):
        try:
            # Llama al archivo conexion.js con Node.js
            resultado = subprocess.run(
                ["node", "/attendance_manager/static/src/js/conexion.js"],  # Ruta al archivo JS
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            
            # La salida de Node.js estará en JSON, así que la parseamos
            datos = json.loads(resultado.stdout)

            # Guarda los datos en el campo "resultado"
            self.create({"resultado": json.dumps(datos)})

            return datos
        except subprocess.CalledProcessError as e:
            # Si ocurre un error al ejecutar el archivo JS, capturamos los detalles
            raise Exception(f"Error al ejecutar el archivo JS: {e.stderr}")
        except json.JSONDecodeError as e:
            # Si hay un problema al decodificar el JSON
            raise Exception(f"Error al decodificar JSON: {e}")

