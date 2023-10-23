# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WizardAporteCapital(models.TransientModel):
    _name = 'prestamos.aporte.capital'
    
    abono = fields.Float("Monto a pagar")
    date = fields.Date("Fecha de pago", default=lambda self : fields.Date.today())

    
    def aportar_capital(self):
        active_id = self.env.context.get('active_id')
        prestamo = self.env['prestamos'].browse(active_id)
        prestamo.re_write_cuotas(self.abono, self.date)