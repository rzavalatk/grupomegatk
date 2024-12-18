from odoo import models, fields, api
import subprocess
import json
import pymssql
import logging
from sqlalchemy import create_engine

_loggin = logging.getLogger(__name__)

class ConexionSQLServer(models.Model):
    _name = "conexion.sqlserver"
    _description = "Conexión a SQL Server desde Odoo"

    resultado = fields.Text("Resultado de la consulta")

    #@api.model
    def obtener_datos_desde_sql(self):
        try:
            _loggin.warning("0")
            # Configuración de conexión
            connection = pymssql.connect(
                server="192.168.10.12",  # Dirección o IP del servidor
                user="anviz",               # Usuario de la base de datos
                password="Megatk2025",        # Contraseña del usuario
                database="COSEC"        # Nombre de la base de datos
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
    
    
    """def obtener_datos_desde_sql(self):
        # Conectar a la base de datos de COSEC
        _loggin.warning("0")
        engine = create_engine('mssql+pymssql://anviz:Megatk2025@192.168.10.12:1433/COSEC')
        _loggin.warning("5")
        with engine.connect() as connection:
            result = connection.execute("SHOW TABLES FROM COSEC")
            for row in result:
                _loggin.warning('row:  ' + str(row))

        _loggin.warning("2")
        conn = pymssql.connect(server='192.168.10.12', user='anviz', password='Megatk2025', database='COSEC')
        cursor = conn.cursor()

        _loggin.warning("3")
        cursor.execute("SELECT * FROM [COSEC].[dbo].[Mx_ATDEventTrn]")
        rows = cursor.fetchall()
        _loggin.warning("4")
        for row in rows:
            _loggin.warning('row:  ' + str(row))

        conn.close()"""