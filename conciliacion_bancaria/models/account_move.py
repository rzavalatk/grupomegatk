# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    
    es_conciliado = fields.Boolean("Conciliado")
    

class AccountMove(models.Model):
    _inherit = "account.move"
    
    es_conciliado = fields.Boolean("Conciliado")
    conciliacion_id = fields.Many2one("conicliacion.bancaria", "Conciliación")

    def unlink(self):
    
        for move in self:
            
            if move.es_conciliado:
                
                raise Warning(_('Desconciliar la conciliación: %s para poder eliminar el movimiento.') % (move.conciliacion_id.name))
        
        
        return super(AccountMove, self).unlink()