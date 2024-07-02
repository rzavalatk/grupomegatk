from odoo import models, fields, api
import math

import base64
import io
from odoo.tools.misc import xlsxwriter

from datetime import timedelta
import time
from dateutil.relativedelta import relativedelta
from datetime import date

class Prestamo(models.Model):
    _name = 'prestamo'
    _description = 'Modelo de Préstamo'

    #Datos generales
    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, readonly=True, states={'borrador': [('readonly', False)]}, copy=False)
    remaining_capital = fields.Monetary('Capital restante', readonly=True,  copy=False,) #Se tiene que crear metodo computado para la asignación constante de cuanto capital queda
    pay_capital = fields.Float('Capital pagado',  readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    note = fields.Text('Notas', readonly=True, states={'borrador': [('readonly', False)]}, copy=False) #Agregar a un campo en una page del notebook
    sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
    
    #Datos del prestamo
    amount_borrowed = fields.Monetary(string='Monto del Préstamo', store=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    #Datos de fechas
    meses_seleccion = fields.Selection(
        [
            ('12', '12 meses'),
            ('24', '24 meses'),
            ('36', '36 meses'),
            ('48', '48 meses'),
            ('60', '60 meses'),
        ],
        string='Duracion (meses)',
        required=True,
        default='12',
        readonly=True, states={'borrador': [('readonly', False)]}
    )
    #duration = fields.Integer(string='Duracion (meses)', required=True, readonly=True, states={'borrador': [('readonly', False)]}) #ESTO TIENE QUE SER UN SELECTION
    date_init = fields.Date(string='Fecha de Inicio', required=True, default=lambda self: date.today()) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    date_end = fields.Date(string='Fecha final', compute='_compute_date_end', store=True)
    
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
    payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago',required=True, readonly=True, states={'borrador': [('readonly', False)]},)
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
        ('financiamiento', 'Financiamiento')
    ], string='Tipo de Préstamo', default="personal", required=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('pagado', 'Pagado')
    ], string='Estado', default='borrador', required=True)
    
    
    quota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas', readonly=True)
    #contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    @api.depends('amount_borrowed', 'quota_ids')
    def _compute_amount_borrowed(self):
        for prestamo in self:
            pagado = 0
            
            for quota in prestamo.quota_ids:
                pagado = pagado + quota.amount_pay
            
            prestamo.amount_borrowed = prestamo.amount_borrowed - pagado
            
    @api.depends('date_init', 'meses_seleccion')
    def _compute_date_end(self):
        for record in self:
            if record.date_init and record.meses_seleccion:
                meses = int(record.meses_seleccion)
                record.date_end = record.date_init + relativedelta(months=meses)
            else:
                record.date_end = False

    
    @api.depends('amount_borrowed', 'interest_rate', 'duration')
    def _compute_amount_cxc(self):
        for prestamo in self:
            prestamo.amount_cxc = prestamo.amount_borrowed * (1 + (prestamo.interest_rate / 100) * (prestamo.duration / 12))

    @api.depends('price_a', 'price_m')
    def _compute_utility(self):
        for prestamo in self:
            prestamo.utility = prestamo.price_a - prestamo.price_m

    @api.depends('price_m', 'prima')
    def _compute_amount_cxp(self):
        for prestamo in self:
            prestamo.amount_cxp = prestamo.price_m - prestamo.prima
            
    @api.depends('price_m', 'prima')
    def _compute_amount_cxp(self):
        for prestamo in self:
            prestamo.amount_cxp = prestamo.price_m - prestamo.prima

    """@api.onchange('quota_ids')
    def _onchange_quota_ids_(self):
        if self.quota_ids:
            pagado = 0
            for quta in self.quota_ids:
                 if quta.state == 'pagado':
                     pagado = pagado + quta.amount_capital_quota
            self.pay_capital = pagado
            self.remaining_capital = self.amount_borrowed - self.pay_capital
            
    @api.onchange('date_init', 'duration')
    def _onchange_dates(self):
        if self.date_init and self.duration:
            start_date = fields.Date.from_string(self.date_init)
            months = int(self.duration)
            self.date_end = start_date + relativedelta(months=months)
        else:
            self.date_end = False

    @api.depends('date_init', 'duration')
    def _compute_end_date(self):
        for record in self:
            if record.date_init and record.duration:
                start_date = fields.Date.from_string(record.date_init)
                months = int(record.duration)
                record.date_end = start_date + relativedelta(months=months)
            else:
                record.date_end = False"""    
    
    def _compute_invoiced(self):
        for prestamo in self:
            prestamo.invoice_count_cxc = len(prestamo.invoice_cxc_ids)
            prestamo.invoice_count_cxp = len(prestamo.quota_ids.filtered(lambda q: q.is_pagado))
            prestamo.payment_count = len(prestamo.payment_ids)
            prestamo.cuotas_count = len(prestamo.quota_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('prestamo') or 'Nuevo'
        return super(Prestamo, self).create(vals)
    
    def date_due_cuota(self, date_init, quta):
        
        if self.payment_frequency == 365:
            return date_init + timedelta(days=1 * quta)
        elif self.payment_frequency == 52:
            return date_init + timedelta(days=7 * quta)
        elif self.payment_frequency == 24:
            return date_init + timedelta(days=15 * quta)
        elif self.payment_frequency == 12:
            return date_init + timedelta(days=30 * quta)
        elif self.payment_frequency == 6:
            return date_init + timedelta(days=60 * quta)
        elif self.payment_frequency == 4:
            return date_init + timedelta(days=90 * quta)
        elif self.payment_frequency == 1:
            return date_init + timedelta(days=365 * quta)
        

    def generate_quota(self):
        for prestamo in self:
            time.sleep(2)
            cuota_obj = self.env['cuota']
            
            # Determinar la frecuencia de pago en número de pagos por año
            frequency_map = {
                '365': 365,
                '52': 52,
                '24': 24,
                '12': 12,
                '6': 6,
                '1': 4,
                '1': 1
            }
            
            if prestamo.payment_frequency not in frequency_map:
                raise ValueError("Frecuencia de pago no válida")
            
            payments_per_year = frequency_map[prestamo.payment_frequency]
            total_payments = payments_per_year * int(prestamo.duration / 12)
            
            saldo_pendiente = prestamo.amount_borrowed
            tasa_interes_mensual = prestamo.interest_rate / 100 / 12
            amortizacion_constante = prestamo.amount_borrowed / total_payments
            
            # Calcular la cuota fija mensual
            cuota_mensual = prestamo.amount_borrowed * (tasa_interes_mensual * (1 + tasa_interes_mensual) ** total_payments) / ((1 + tasa_interes_mensual) ** total_payments - 1)

            time.sleep(2)
            for cuota_number in range(1, total_payments + 1):
                
                interes = saldo_pendiente * tasa_interes_mensual
                
                capital_amortizado = cuota_mensual - interes
                saldo_pendiente -= capital_amortizado

                cuota_obj.create({
                    'name': f'Cuota {cuota_number}/{total_payments} de {prestamo.name}',
                    'prestamo_id': prestamo.id,
                    'amount': cuota_mensual,
                    'amount_capital_quota': capital_amortizado,
                    'amount_capital': saldo_pendiente,
                    'interest_rate': prestamo.interest_rate,
                    'interest_generated': interes,
                    'date_due': self.date_due_cuota(prestamo.date_init, total_payments),
                })
                
             

        
            
            """# Determinar la frecuencia de pago en número de pagos por año
            frequency_map = {
                '365': 365,
                '52': 52,
                '24': 24,
                '12': 12,
                '6': 6,
                '1': 4,
                '1': 1
            }
            
            if prestamo.payment_frequency not in frequency_map:
                raise ValueError("Frecuencia de pago no válida")
            
            payments_per_year = frequency_map[prestamo.payment_frequency]
            total_payments = payments_per_year * int(prestamo.duration / 12)
            At = prestamo.amount_borrowed / total_payments
            tasa_interes = prestamo.interest_rate / 100
            n = 0
            
            for quta in range(1, total_payments + 1):
                
                St = prestamo.amount_borrowed - (n * At)
                
                Tim = tasa_interes / 12
                Tim1 = 1 + Tim
                
                exp = pow(Tim1, 12)
                
                It = (St * tasa_interes) - St
                
                Ct = At + It
                
                cuota_obj.create({
                    'name': f'Cuota {quta}/{total_payments} de {prestamo.name}',
                    'prestamo_id': prestamo.id,
                    'amount': Ct,
                    'amount_capital': St,
                    'interest_rate': prestamo.interest_rate,
                    'interest_generated': It,
                    'date_due': self.date_due_cuota(prestamo.date_init, quta),
                })
                
                n = n + 1"""

    def action_approve(self):
        for prestamo in self:
            prestamo.state = 'aprobado'
            prestamo.generate_quota()

    def action_reject(self):
        for prestamo in self:
            prestamo.state = 'rechazado'

    def action_pay(self):
        for prestamo in self:
            prestamo.state = 'pagado'
            
            
    

    """def calculate_quotas(self):
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
            return fields.Date.add(date, years=1)"""

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