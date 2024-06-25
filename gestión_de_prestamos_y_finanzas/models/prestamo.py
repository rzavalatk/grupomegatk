from odoo import models, fields, api
import math

import base64
import io
from odoo.tools.misc import xlsxwriter

from datetime import timedelta
import time
from dateutil.relativedelta import relativedelta

class Prestamo(models.Model):
    _name = 'prestamo'
    _description = 'Modelo de Préstamo'

    #Datos generales
    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, readonly=True, states={'borrador': [('readonly', False)]}, copy=False)
   
    
    #Datos del prestamo
    amount_borrowed = fields.Float(string='Monto del Préstamo', store=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    #Datos de fechas
    duration = fields.Integer(string='Duracion (meses)', required=True, readonly=True, states={'borrador': [('readonly', False)]}) #ESTO TIENE QUE SER UN SELECTION
    date_init = fields.Date(string='Fecha de Inicio', required=True) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    date_end = fields.Date(string='Fecha final', required=True) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    
    #Datos de cuentas bancarias
    
   
    loan_type = fields.Selection([
        ('personal', 'Personal'),
        ('refinanciado', 'Refinanciado'),
        ('financiamiento', 'Financiamiento')
    ], string='Tipo de Préstamo', required=True)
    
    
    
    #quota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas', readonly=True)
    #contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    