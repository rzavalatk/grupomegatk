# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ResUsers(models.Model):
	_inherit = "res.users"

	tipo_vendedor = fields.Selection([('1','Calle'),('2','Tienda')], string='Tipo de Vendedor' )
	ubicacion_vendedor = fields.Selection([('1','NIC'),('2','SPS'),('3','TGU')], string='Ubicación')
	empresa_pertenece = fields.Selection([('megatk','Megatk'),('meditek','Meditek'),('printex','Printex'),('lenka','Lenka'),('mediteksa','Mediteksa Nic')], string='Empresa')
