import pymssql
from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

from odoo.exceptions import UserError

class SQLServerConnection(models.Model):
    _name = 'sql.server.connection'
    _description = 'SQL Server Connection Example'

    name = fields.Char(string='Connection Name', required=True)
    server = fields.Char(string='SQL Server IP', required=True)
    database = fields.Char(string='Database Name', required=True)
    username = fields.Char(string='Username', required=True)
    password = fields.Char(string='Password', required=True)

    def button_test_connection(self):
        """Método para probar la conexión desde un botón."""
        try:
            connection = pymssql.connect(
                server=self.server,
                user=self.username,
                password=self.password,
                database=self.database
            )
            connection.close()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Conexión exitosa',
                    'message': 'Conexión a SQL Server realizada con éxito.',
                    'sticky': False,
                },
            }
        except Exception as e:
            raise UserError(f"Error al conectar con SQL Server: {e}")
