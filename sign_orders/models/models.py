# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime


class SignOrders(models.Model):
    _inherit = 'stock.picking'


    passed = fields.Char(string="Aprobado")
    color = fields.Integer(default=1234)
    current_user = fields.Many2one('res.users', compute='_get_current_user')

    @api.depends()
    def _get_current_user(self):
        self.update({'current_user' : self.env.user.id})

    @api.multi
    def _automate_color(self):
        print("////////////////Inicio del coloreo Kanban, module:sign_orders, model:stock.picking /////////////")
        data = self.env['stock.picking'].sudo().search([('passed','=','No')])
        dt = datetime.today()
        strDate = dt.strftime("%d/%m/%Y")
        truncDate = datetime.strptime(strDate+" 00:00:00", "%d/%m/%Y %H:%M:%S")
        for item in data:
            self = self.browse(item.id)
            if item.scheduled_date < truncDate:
                self.write({'color': 1})
            else:
                self.write({'color': 4})
        print("////////////////Fin del coloreo Kanban, module:sign_orders, model:stock.picking /////////////")
        return True

