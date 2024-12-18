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

    
    def obtener_datos_desde_sql(self):
        try:

            # Connection Parameters
            my_server = "192.168.10.12"
            my_user = "anviz"
            my_database = "COSEC"
            my_password = "Megatk2025"
            my_query = """SELECT TABLE_NAME 
                        FROM INFORMATION_SCHEMA.TABLES 
                        WHERE TABLE_TYPE = 'BASE TABLE' 
                        ORDER BY TABLE_NAME;
                        """

            # Make the connection and execute the query
            conn = pymssql.connect(server=my_server, user=my_user, password=my_password, database=my_database)
            cursor = conn.cursor()
            cursor.execute(my_query)

            # Check whether the query is a select statement or an insert/update/delete instruction
            if my_query.strip().split(" ")[0].lower() == "select":
                rows = cursor.fetchall()
                my_result = ""
                for i in rows:
                    for x in i:
                        my_result += "\t" + str(x)
                    my_result += "\n"

                # Show the result
                self.resultado = my_result
            else:
                conn.commit()
                self.resultado = "Statement executed successfully, please check your database or make a select statement."
            conn.close()

        except:
            self.resultado = "An Error Occurred, please check your parameters!\n" \
                          "And make sure (pymssql) is installed (pip3 install pymssql)."

    #@api.model
    """def obtener_datos_desde_sql(self):
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
            _loggin.error("Error al conectar a la base de datos SQL Server:", e)"""
    
    
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