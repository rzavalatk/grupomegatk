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
    disbursal_amount = fields.Float(string="Disbursal_amount",
                                    help="Total loan amount "
                                         "available to disburse")
    
    #Datos del prestamo
    amount_borrowed = fields.Monetary(string='Monto del Préstamo', store=True, readonly=True, states={'borrador': [('readonly', False)]},)
    cuota = fields.Monetary('Cuota', readonly=True,  copy=False,)
    loan_type_id = fields.Many2one('loan.type', string='Tipo de prestamo', required=True)
    documents_ids = fields.Many2many('loan.documents', string="Documentos",)
    img_attachment_ids = fields.Many2many('ir.attachment', relation="m2m_ir_identity_card_rel",column1="documents_ids",string="Imagenes",)
    reject_reason = fields.Text(string="Razon de rechazo")
    request = fields.Boolean(string="Request", default=False,help="Para monitorear el prestamo")
    
    #Datos de fechas
    meses_seleccion = fields.Selection(
        [
            ('12', '12 meses'),
            ('24', '24 meses'),
            ('36', '36 meses'),
            ('48', '48 meses'),
            ('60', '60 meses'),
        ],
        string='Duracion (meses)', required=True, default='12', readonly=True, states={'borrador': [('readonly', False)]})
    date_init = fields.Date(string='Fecha de Inicio', required=True, default=lambda self: date.today(), readonly=True, states={'borrador': [('readonly', False)]},) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    date_ends = fields.Date(string='Fecha final', compute='_compute_date_ends', store=True)
    
    #Datos de cuentas bancarias
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id, readonly=True, states={'borrador': [('readonly', False)]},)
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type', '=', 'bank')], required=True,)
    account_id = fields.Many2one('account.account', 'Cuenta de intereses', required=True)
    account_int_moratorio = fields.Many2one('account.account', 'Cuenta de intereses moratorios', required=True)
    account_gasto_id = fields.Many2one('account.account', 'Cuenta de gastos', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    user_id = fields.Many2one('res.users', string='Responsable', index=True, default=lambda self: self.env.user, readonly=True, states={'draft': [('readonly', False)]},)
    debit_account_id = fields.Many2one('account.account', string="Cuenta de debito", help="Elija cuenta para débito por desembolso")
    credit_account_id = fields.Many2one('account.account', string="Cuenta de credito", help="Elija cuenta para credito por desembolso")
    
    
    #Datos de contabilidad
    payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago',required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    interest_rate = fields.Integer(string='Tasa de Interés', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True, states={'borrador': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    gasto_prestamo = fields.Monetary(string='Gastos administrativos', default=0, readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    
    #Variables de conteo
    invoice_count_cxc = fields.Integer(string='Factura Count', compute='_compute_invoiced', readonly=True)
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
    ], string='Frecuencia de Pago', default='12', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    loan_type = fields.Selection([
        ('personal', 'Personal'),
        ('financiamiento', 'Financiamiento')
    ], string='Tipo de Préstamo', default="personal", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('generado', 'Generado'),
        ('confirmado', 'Confirmado'),
        ('aprobado', 'Aprobado'),
        ('pro_pago', 'Proceso de pago')
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        ('pagado', 'Pagado')
    ], string='Estado', default='borrador', required=True)
       
    
    quota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas', readonly=True)
    #contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    
   