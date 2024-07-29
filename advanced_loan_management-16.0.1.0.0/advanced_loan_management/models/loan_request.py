# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math

import base64
import io
from odoo.tools.misc import xlsxwriter
from odoo.exceptions import UserError

from datetime import timedelta
import time
from dateutil.relativedelta import relativedelta
from datetime import date

class Prestamo(models.Model):
    """Aqui se crearan los prestamos y se manejaran las cuotas"""
    _name = 'prestamo'
    _inherit = ['mail.thread']
    _description = 'Modelo de Préstamo'

    #Datos generales
    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, readonly=True, states={'borrador': [('readonly', False)]}, copy=False)
    remaining_capital = fields.Monetary('Capital restante', readonly=True,  copy=False,) #Se tiene que crear metodo computado para la asignación constante de cuanto capital queda
    pay_capital = fields.Monetary('Capital pagado',  readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    note = fields.Text('Notas', readonly=True, states={'borrador': [('readonly', False)]}, copy=False) #Agregar a un campo en una page del notebook
