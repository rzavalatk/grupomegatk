# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import Warning
import requests


class SorteoTicket(models.Model):
    _name = 'sorteo.ticket'
    _description = 'Tickets para el sorteo'

    """def get_name_tick(self):
        
       if self.sorteo:
            flag = False
            if not self.cheque_anulado:
                for seq in self.journal_id.secuencia_ids:
                    if seq.move_type == self.doc_type:
                        self.number_calc = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
                        flag = True
                        break  # Agregamos un break para salir del bucle cuando encontramos una secuencia válida
                if not flag:
                    self.msg = "No existe numeración para este banco, verifique la configuración"
                    self.number_calc = ""
                else:
                    self.msg = ""
            else:
                self.msg = "El cheque está anulado"  # Mensaje adicional si el cheque está anulado"""
       
    
    name = fields.Char(string='Número de Ticket', copy=False)
    move_id = fields.Many2one('account.move', string='Factura')
    customer_id = fields.Many2one('res.partner', string='Cliente', store=True)
    sorteo = fields.Many2one('sorteo.sorteo', string='Sorteo', store=True) 
    email = fields.Char(string='Correo Electrónico', related='customer_id.email', store=True)
    telefono = fields.Char(string='Telefono', related='customer_id.phone', store=True)
    move_line_id = fields.Char(string='move line id')
    fecha = fields.Date(string='fecha')
    
    """@api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('ticket.sequence')

        return super(SorteoTicket, self).create(vals_list)
    
    @api.model
    def create(self, vals):
        
            if vals.get('session_number', ('50000')) == ('50000'):
                vals['session_number'] = self.env['ir.sequence'].next_by_code('session.number')
        return super().create(vals)
    """
    
    

