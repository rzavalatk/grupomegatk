from odoo import models, fields, api
import subprocess
import json
import pymssql
import logging

_loggin = logging.getLogger(__name__)

class ConexionSQLServer(models.Model):
    _name = "conexion.sqlserver"
    _description = "Conexión a SQL Server desde Odoo"

    resultado = fields.Text("Resultado de la consulta")

    #@api.model
    def obtener_datos_desde_sql(self):
        try:
            # Configuración de conexión
            connection = pymssql.connect(
                server="192.168.10.12",  # Dirección o IP del servidor
                user="sa",               # Usuario de la base de datos
                password="M3g@tK2012",        # Contraseña del usuario
                database="Megatk_Sistema"        # Nombre de la base de datos
            )
            cursor = connection.cursor()
            _loggin.warning("1")

            # Ejecutar una consulta
            cursor.execute("SELECT * FROM tabla_ejemplo;")
            registros = cursor.fetchall()
            _loggin.warning("2")

            for registro in registros:
                _loggin.info(registro)

            # Cerrar la conexión
            cursor.close()
            connection.close()
            
            _loggin.warning("3")

        except Exception as e:
            _loggin.error("Error al conectar a la base de datos SQL Server:", e)