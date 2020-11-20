# -*- encoding: utf-8 -*-
from odoo import fields, models, exceptions, api, _
import base64
import csv
#import cStringIO
from io import StringIO
from odoo.exceptions import except_orm, Warning


class ImportInventory(models.TransientModel):
    _name = "lista.precios.import.megatk"


    data = fields.Binary('Documento', required=True)
    delimeter = fields.Char('Delimeter', default=',', help='Default delimeter is ","')


    @api.one
    def action_import(self):
        ctx = self._context
        import_obj = self.env["lista.precios.megatk"]
        obj_line_data = self.env["lista.precios.megatk.line"]
        product_obj = self.env["product.product"]
        if 'active_id' in ctx:
            importar = import_obj.browse(ctx['active_id'])
        if not self.data:
            raise exceptions.Warning(_("Seleccione un archivo!"))
        data = base64.b64decode(self.data)
        file_input = io.StringIO(data)
        file_input.seek(0)
        reader_info = []
        delimeter = ','
        reader = csv.reader(file_input, delimiter=delimeter, lineterminator='\r\n')
        try:
            reader_info.extend(reader)
        except Exception:
            raise exceptions.Warning(_("Archivo no valido!"))
        keys = reader_info[0]
        if not isinstance(keys, list) or ('code' not in keys):
            raise exceptions.Warning(_("No se encontraron 'códigos' de productos"))
        del reader_info[0]
        values = {}
        for i in range(len(reader_info)):
            vals = {}
            field = reader_info[i]
            values = dict(zip(keys, field))
            tmp_val = product_obj.search([("default_code", "=", values['code'])])
            if len(tmp_val) > 1:
                raise exceptions.Warning(_("Existen productos con codigos repetidos"))
            if tmp_val:
                vals = {
                    'obj_padre': importar.id,
                    'precio_publico': tmp_val.list_price,
                    'product_id': tmp_val.id,
                }
                obj_line_data.create(vals)
