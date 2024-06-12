from odoo import models, fields, api
import math

import base64
import io
from odoo.tools.misc import xlsxwriter

class Prestamo(models.Model):
    _name = 'prestamo'
    _description = 'Modelo de Préstamo'

    #Datos generales
    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True)
    remaining_capital = fields.Float('Capital restante',  copy=False,)
    note = fields.Text('Notas', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
    
    #Datos del prestamo
    amount_borrowed = fields.Float(string='Monto del Préstamo', store=True, readonly=True, states={'draft': [('readonly', False)]},)
    
    #Datos del financiamiento
    amount_cxc = fields.Float(string='Monto a financiar', compute='_onchange_precio', store=True, readonly=True, states={'draft': [('readonly', False)]},)
    
    #Datos de financiamiento / producto
    supplier_id = fields.Many2one('res.partner', string='Proveedor', required=True)
    equipment = fields.Many2one('product.product', string='Equipo financiado', readonly=True, states={'draft': [('readonly', False)]},)
    price_a = fields.Float(string='Precio A', readonly=True, states={'draft': [('readonly', False)]},)
    price_m = fields.Float(string='Precio M', readonly=True, states={'draft': [('readonly', False)]},)
    prima = fields.Float(string='Prima', readonly=True, states={'draft': [('readonly', False)]},)
    utility = fields.Float(string='Utilidad', compute='_onchange_precioa_preciom', readonly=True, states={'draft': [('readonly', False)]},)
    amount_cxp = fields.Float(string='Monto a pagar', compute='_onchange_preciom_prima', readonly=True, states={'draft': [('readonly', False)]},)
    
    #Datos de fechas
    duration = fields.Integer(string='Duración (meses)', required=True)
    date_init = fields.Date(string='Fecha de Inicio', required=True)
    date_end = fields.Date(string='Fecha final', required=True)
    
    #Datos de cuentas bancarias
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id, readonly=True, states={'draft': [('readonly', False)]},)
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type', '=', 'bank')], required=True,)
    producto_gasto_id = fields.Many2one('product.product', string='Cuenta de gasto', required=True, domain=[('sale_ok', '=', True)], default=product_gasto,)
    producto_interes_id = fields.Many2one('product.product', string='Cuenta de interes', required=True, domain=[('sale_ok', '=', True)], default=product_interes,)
    account_id = fields.Many2one('account.account', 'Cuenta de desembolso', required=True, default=desembolso_cuenta,)
    account_redes_id = fields.Many2one('account.account', 'Cuenta de redescuento', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=redescuento_cuenta)
    user_id = fields.Many2one('res.users', string='Responsable', index=True,default=lambda self: self.env.user, readonly=True, states={'draft': [('readonly', False)]},)
    
    #Datos de contabilidad
    payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago',required=True, readonly=True, states={'draft': [('readonly', False)]},)
    meses_cred = fields.Integer(string='Mes', required=True, readonly=True, states={'draft': [('readonly', False)]})
    interest_rate = fields.Float(string='Tasa de Interés', required=True)
    currency_id = fields.Many2one('res.currency', 'Moneda', default=lambda self: self.env.user.company_id.currency_id.id,readonly=True, states={'draft': [('readonly', False)]},)
    
    #Variables de conteo
    invoice_count_cxc = fields.Integer(string='Factura Count', compute='_get_invoiced', readonly=True)
    invoice_count_cxp = fields.Integer(string='Factura Count', compute='_get_invoiced', readonly=True)
    payment_count = fields.Integer(string='Payment Count', compute='_get_invoiced', readonly=True)
    cuotas_count = fields.Integer(string='cuotas Count', compute='_get_invoiced', readonly=True)
    invoice_cxc_ids = fields.Many2many("account.move", string='Facturas cxc', readonly=True, copy=False)
    payment_ids = fields.Many2many("account.payment", string="Pagos", copy=False,)
       
    payment_frequency = fields.Selection([
        ('diario', 'Diario'),
        ('semanal', 'Semanal'),
        ('quincenal', 'Quincenal'),
        ('mensual', 'Mensual'),
        ('bimestral', 'Bimestral'),
        ('trimestral', 'Trimestral'),
        ('anual', 'Anual')
    ], string='Frecuencia de Pago', default='mensual', required=True)
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
    
    
    quota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas')
    #contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('prestamo') or 'Nuevo'
        result = super(Prestamo, self).create(vals)
        result.calculate_quotas()
        return result

    def calculate_quotas(self):
        for prestamo in self:
            cantidad_cuotas = prestamo.duration #Cantidad de meses = cantidad de cuotas para pagos mensuales
            monto_cuota = self.calculate_amount_quotas(prestamo.amount_borrowed, prestamo.interest_rate, prestamo.duration)
            fecha_cuota = prestamo.date_init
            for i in range(1, cantidad_cuotas + 1):
                self.env['cuota'].create({
                    'prestamo_id': prestamo.id,
                    'amount': monto_cuota,
                    'date_due': fecha_cuota,
                })
                fecha_cuota = self.add_period(fecha_cuota, prestamo.payment_frequency)

    def calculate_amount_quotas(self, amount, tasa, duration):
        tasa_mensual = (tasa / 100) / 12
        return amount * tasa_mensual / (1 - (1 + tasa_mensual) ** -duration)

    def add_period(self, date, frequency):
        if frequency == 'diario':
            return fields.Date.add(date, days=1)
        elif frequency == 'semanal':
            return fields.Date.add(date, weeks=1)
        elif frequency == 'quincenal':
            return fields.Date.add(date, days=15)
        elif frequency == 'mensual':
            return fields.Date.add(date, months=1)
        elif frequency == 'bimestral':
            return fields.Date.add(date, months=2)
        elif frequency == 'trimestral':
            return fields.Date.add(date, months=3)
        elif frequency == 'anual':
            return fields.Date.add(date, years=1)

    def export_excel(self):
        # Crear un archivo en memoria
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        # Escribir datos en el archivo Excel
        worksheet.write(0, 0, 'Número de Préstamo')
        worksheet.write(0, 1, 'Cliente')
        worksheet.write(0, 2, 'Monto')
        worksheet.write(0, 3, 'Tasa de Interés')
        worksheet.write(0, 4, 'Duración (meses)')
        worksheet.write(0, 5, 'Fecha de Inicio')
        worksheet.write(0, 6, 'Frecuencia de Pago')
        worksheet.write(0, 7, 'Tipo de Préstamo')

        row = 1
        for prestamo in self:
            worksheet.write(row, 0, prestamo.name)
            worksheet.write(row, 1, prestamo.partner_id.name)
            worksheet.write(row, 2, prestamo.amount_borrowed)
            worksheet.write(row, 3, prestamo.interest_rate)
            worksheet.write(row, 4, prestamo.duration)
            worksheet.write(row, 5, str(prestamo.date_init))
            worksheet.write(row, 6, dict(prestamo._fields['payment_frequency'].selection).get(prestamo.payment_frequency))
            worksheet.write(row, 7, dict(prestamo._fields['loan_type'].selection).get(prestamo.loan_type))
            row += 1

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        # Crear el adjunto en Odoo y devolver el enlace de descarga
        attachment = self.env['ir.attachment'].create({
            'name': f'Prestamo_{self.name}.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'store_fname': f'Prestamo_{self.name}.xlsx',
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }