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
    remaining_capital = fields.Float('Capital restante', readonly=True, states={'borrador': [('readonly', False)]},  copy=False,) #Se tiene que crear metodo computado para la asignación constante de cuanto capital queda
    pay_capital = fields.Float('Capital pagado',  readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    note = fields.Text('Notas', readonly=True, states={'borrador': [('readonly', False)]}, copy=False) #Agregar a un campo en una page del notebook
    sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
    
    #Datos del prestamo
    amount_borrowed = fields.Float(string='Monto del Préstamo', store=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    #Datos de fechas
    duration = fields.Integer(string='Duracion (meses)', required=True, readonly=True, states={'borrador': [('readonly', False)]}) #ESTO TIENE QUE SER UN SELECTION
    date_init = fields.Date(string='Fecha de Inicio', required=True) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    date_end = fields.Date(string='Fecha final', required=True) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    
    #Datos de cuentas bancarias
    
    #ESTO ESTA POR DEFINIRSE
    
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id, readonly=True, states={'borrador': [('readonly', False)]},)
    #recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type', '=', 'bank')], required=True,)
    """producto_gasto_id = fields.Many2one('product.product', string='Cuenta de gasto', required=True, domain=[('sale_ok', '=', True)], default=product_gasto,)
    producto_interes_id = fields.Many2one('product.product', string='Cuenta de interes', required=True, domain=[('sale_ok', '=', True)], default=product_interes,)
    account_id = fields.Many2one('account.account', 'Cuenta de desembolso', required=True, default=desembolso_cuenta,)
    account_redes_id = fields.Many2one('account.account', 'Cuenta de redescuento', required=True, readonly=True, states={'borrador': [('readonly', False)]}, default=redescuento_cuenta)"""
    user_id = fields.Many2one('res.users', string='Responsable', index=True,default=lambda self: self.env.user, readonly=True, states={'borrador': [('readonly', False)]},)
    
    #Datos de contabilidad
    payment_term_id = fields.Many2one('account.payment.term|', string='Plazo de pago',required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    meses_cred = fields.Integer(string='Mes', required=True, readonly=True, states={'borrador': [('readonly', False)]})
    interest_rate = fields.Float(string='Tasa de Interés', required=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True, states={'borrador': [('readonly', False)]},)
    
    #Variables de conteo
    invoice_count_cxc = fields.Integer(string='Factura Count', compute='_compute_invoiced', readonly=True)
    invoice_count_cxp = fields.Integer(string='Factura Count', compute='_compute_invoiced', readonly=True)
    payment_count = fields.Integer(string='Payment Count', compute='_compute_invoiced', readonly=True)
    cuotas_count = fields.Integer(string='cuotas Count', compute='_compute_invoiced', readonly=True)
    invoice_cxc_ids = fields.Many2many("account.move", string='Facturas cxc', readonly=True, copy=False)
    payment_ids = fields.Many2many("account.payment", string="Pagos", copy=False,)
       
    payment_frequency = fields.Selection([
        ('365', 'Diario'),
        ('52', 'Semanal'),
        ('24', 'Quincenal'),
        ('12', 'Mensual'),
        ('6', 'Bimestral'),
        ('4', 'Trimestral'),
        ('1', 'Anual')
    ], string='Frecuencia de Pago', default='12', required=True)
    loan_type = fields.Selection([
        ('personal', 'Personal'),
        ('refinanciado', 'Refinanciado'),
        ('financiamiento', 'Financiamiento')
    ], string='Tipo de Préstamo', required=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('pagado', 'Pagado')
    ], string='Estado', default='borrador', required=True)
    
    
    quota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas', readonly=True)
    #contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    