# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import Warning


class Consults(models.Model):
    _name = 'consultas.custom'
    _description = """
        Modelo para correr consultas directamente a la base
    """
    
    name = fields.Char("Titulo")
    col = fields.Char("Columnas")
    query = fields.Text("Consulta")
    
    def execute_query(self):
        try:
            self.env.cr.execute(self.query)
            return True
        except Exception as inst:
            raise Warning('Error en la consulta: ' + inst.args[0])

        
    def generate_report(self):
        try:
            self.env.cr.execute(self.query)
            data = self.env.cr.fetchall()
            csv = f"""{self.col},\n"""
            if len(data) > 0:
                for row in data:
                    csv_row = ""
                    for item in row:
                        item = str(item)
                        item = item.replace('	', '')
                        temp = item.replace(',', '')
                        csv_row+= "{},".format(temp)
                    csv+="{}\n".format(csv_row[:-1])
            return csv
        except Exception as inst:
            raise Warning('Error en la consulta: ' + inst.args[0])