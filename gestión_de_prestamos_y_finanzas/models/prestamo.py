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
    _name = 'prestamo'
    _description = 'Modelo de Préstamo'

    #Datos generales
    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string='Cliente', required=True, readonly=True, states={'borrador': [('readonly', False)]}, copy=False)
    remaining_capital = fields.Monetary('Capital restante', readonly=True,  copy=False,) #Se tiene que crear metodo computado para la asignación constante de cuanto capital queda
    pay_capital = fields.Monetary('Capital pagado',  readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    note = fields.Text('Notas', readonly=True, states={'borrador': [('readonly', False)]}, copy=False) #Agregar a un campo en una page del notebook
    #sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
    
    #Datos del prestamo
    amount_borrowed = fields.Monetary(string='Monto del Préstamo', store=True, readonly=True, states={'borrador': [('readonly', False)]},)
    cuota = fields.Monetary('Cuota', readonly=True,  copy=False,)
    
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
    date_init = fields.Date(string='Fecha de Inicio', required=True, default=lambda self: date.today(), readonly=True, states={'borrador': [('readonly', False)]},) #SE TIENE QUE CALCULAR AUTOMATICO CUANDO SE ELIJE DURACION
    date_ends = fields.Date(string='Fecha final', compute='_compute_date_ends', store=True)
    
    #Datos de cuentas bancarias
    
    company_id = fields.Many2one('res.company', string='Company', change_default=True, required=True, default=lambda self: self.env.user.company_id, readonly=True, states={'borrador': [('readonly', False)]},)
    recibir_pagos = fields.Many2one("account.journal", "Recibir pagos",  domain=[('type', '=', 'bank')], required=True,)
    account_id = fields.Many2one('account.account', 'Cuenta de intereses', required=True)
    account_int_moratorio = fields.Many2one('account.account', 'Cuenta de intereses moratorios', required=True)
    account_redes_id = fields.Many2one('account.account', 'Cuenta de gastos', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    user_id = fields.Many2one('res.users', string='Responsable', index=True,
                              default=lambda self: self.env.user, readonly=True, states={'draft': [('readonly', False)]},)
    
    #Datos de contabilidad
    payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago',required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    interest_rate = fields.Integer(string='Tasa de Interés', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    currency_id = fields.Many2one('res.currency', 'Moneda', readonly=True, states={'borrador': [('readonly', False)]},)
    gasto_prestamo = fields.Monetary(string='Gastos administrativos', default=0, readonly=True, states={
                                  'borrador': [('readonly', False)]}, copy=False,)
    
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
        ('aprobado', 'Aprobado'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        ('pagado', 'Pagado')
    ], string='Estado', default='borrador', required=True)
       
    
    quota_ids = fields.One2many('cuota', 'prestamo_id', string='Cuotas', readonly=True)
    #contrato_id = fields.Many2one('contrato', string='Contrato')
    #garantia_ids = fields.One2many('garantia', 'prestamo_id', string='Garantías')

    #           METODOS COMPUTADOS PARA ASIGNACION DE VALORES
    @api.depends('amount_borrowed', 'quota_ids')
    def _compute_amount_borrowed(self):
        for prestamo in self:
            pagado = 0
            
            for quota in prestamo.quota_ids:
                pagado = pagado + quota.amount_pay
            
            prestamo.amount_borrowed = prestamo.amount_borrowed - pagado
            
    @api.depends('date_init', 'meses_seleccion')
    def _compute_date_ends(self):
        for record in self:
            if record.date_init and record.meses_seleccion:
                meses = int(record.meses_seleccion)
                record.date_ends = record.date_init + relativedelta(months=meses)
            else:
                record.date_ends = False

    
    @api.depends('amount_borrowed', 'interest_rate', 'meses_seleccion')
    def _compute_amount_cxc(self):
        for prestamo in self:
            prestamo.amount_cxc = prestamo.amount_borrowed * (1 + (prestamo.interest_rate / 100) * (prestamo.meses_seleccion / 12))

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
    
    def _compute_invoiced(self):
        for prestamo in self:
            prestamo.invoice_count_cxc = len(prestamo.invoice_cxc_ids)
            prestamo.payment_count = len(prestamo.payment_ids)
            prestamo.cuotas_count = len(prestamo.quota_ids)
            
    
    #           METODOS ONCHANGE
    """@api.onchange('amount_borrowed')
    def _onchange_amount_borrowed(self):
        for prestamo in self:
            prestamo.amount_borrowed = self.amount_borrowed"""
        
    @api.onchange('meses_seleccion')
    def _onchange_meses_seleccion(self):
        for prestamo in self:
            prestamo.meses_seleccion = self.meses_seleccion

    #            METODOS CRUD
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('prestamo') or 'Nuevo'
        return super(Prestamo, self).create(vals)
    
    def unlink(self):
        for prestamo in self:
            if prestamo.state != 'draft':
                raise UserError(_('No se puede eliminar o cancelar una prestamo en estado ' + prestamo.state))
        return super(Prestamo, self).unlink()
    
    #            METODOS DE ACCIONES DE ESTADOS
    
    def action_approve(self):
        self.crear_factura()
        for prestamo in self:
            prestamo.state = 'aprobado'

    def action_reject(self):
        for prestamo in self:
            prestamo.state = 'rechazado'
        
    def action_cancel(self):
        cuotas = self.env["cuota"].search(
            [('prestamo_id', '=', self.id)])
        if cuotas:
            for cuota in cuotas:
                if cuota.state != 'draft':
                    raise UserError(_('No se puede eliminar o cancelar un prestamo en estado de ' + self.state))
                cuota.sudo().unlink()         

        self.write({'state': 'cancelado',
                    'cuota_prestamo': 0,
                    'cuota_inicial': 0
                    })
            
    def go_to_draft(self):
        for prestamo in self:
            prestamo.state = 'borrador'
    

    def action_pay(self):
        for prestamo in self:
            prestamo.state = 'pagado'
        
    def ending(self):
        pase = True
        for prestamo in self:
            cuotas = self.env['cuota'].search([('prestamo_id', '=', prestamo.id)])
            for cuota in cuotas:
                if cuota.state != 'pay':
                    pase = False
        if self.amount_borrowed < 1 and pase:
            self.write({
                'state': 'pagado',
            })
        else:
           raise UserError(_('No se puede finalizar el prestamo'))
    
    def unclick_quotas(self):
        for prestamo in self:
            cuotas = self.env['cuota'].search([('prestamo_id', '=', prestamo.id)])
            for cuota in cuotas:
                cuota.unlink()
            prestamo.state = 'borrador'
    
    def date_due_cuota(self, date_init, payments, frequency, n):
        
        if frequency == 365 and n <= payments:
            return date_init + relativedelta(days=1*n)
        elif frequency == 52 and n <= payments:
            return date_init + relativedelta(days=7 * n)
        elif frequency == 24 and n <= payments:
            return date_init + relativedelta(days=15 * n)
        elif frequency == 12 and n <= payments:
            return date_init + relativedelta(months=1 * n)
        elif frequency == 6 and n <= payments:
            return date_init + relativedelta(months=2 * n)
        elif frequency == 4 and n <= payments:
            return date_init + relativedelta(months=3 * n)
        elif frequency == 1 and n <= payments:
            return date_init + relativedelta(months=12 * n)      

    def generate_quota(self):
        for prestamo in self:
            
            if prestamo.interest_rate > 0:
                if prestamo.amount_borrowed <= 0:
                    raise UserError(_("No se puede procesar el prestamo, monto menor que cero o es cero."))
                if not prestamo.name:
                    prestamo.name = self.env['ir.sequence'].next_by_code('prestamo') or 'Nuevo'
                else:
                    time.sleep(2)
                    cuota_obj = self.env['cuota']
                    
                    # Determinar la frecuencia de pago en número de pagos por año
                    frequency_map = {
                        '365': 365,
                        '52': 52,
                        '24': 24,
                        '12': 12,
                        '6': 6,
                        '4': 4,
                        '1': 1
                    }
                    
                    if prestamo.payment_frequency not in frequency_map:
                        raise ValueError("Frecuencia de pago no válida")
                    
                    payments_per_year = frequency_map[prestamo.payment_frequency]
                    total_payments = int(payments_per_year) * (int(prestamo.meses_seleccion) / 12)
                    
                    saldo_pendiente = prestamo.amount_borrowed
                    tasa_interes_mensual = prestamo.interest_rate / 100 / 12
                    amortizacion_constante = prestamo.amount_borrowed / total_payments
                    
                    # Calcular la cuota fija mensual
                    cuota_mensual = prestamo.amount_borrowed * (tasa_interes_mensual * (1 + tasa_interes_mensual) ** total_payments) / ((1 + tasa_interes_mensual) ** total_payments - 1)
                    prestamo.cuota = cuota_mensual
                    n = 1
                    
                    time.sleep(2)
                    for cuota_number in range(1, int(total_payments) + 1):
                        
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
                            'date_due': self.date_due_cuota(prestamo.date_init, total_payments, payments_per_year, n),
                        })
                        
                        if n <= total_payments:
                            n = n + 1
                    
                    prestamo.state = 'generado'
            else:
                 raise UserError(_("La tasa no puede ser menor que cero"))
    
    def crear_factura(self):
        if not self.invoice_cxc_ids:
            self.crear_factura_cxc()
            self.write({
                'remaining_capital': self.amount_borrowed
            })

    def crear_factura_cxc(self):
        obj_factura = self.env["account.move"]
        lineas = []
        val_lineas = {
            'name': 'Capital prestado',
            'account_id': self.recibir_pagos.id,
            'price_unit': self.amount_borrowed,
            'quantity': 1,
            'product_id': False,
            'x_user_id': self.env.user.id
        }
        lineas.append((0, 0, val_lineas))
        if self.gasto_prestamo > 0:
            val_lineas1 = {
                'name': 'Cargos administrativos',
                'account_id': self.account_redes_id.id,
                'price_unit': self.gasto_prestamo,
                'quantity': 1,
                'product_id': False,
                'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas1))
        company_id = self.company_id.id
        journal_id = self.recibir_pagos
        if not journal_id:
            raise UserError(
                _('Please define an accounting sales journal for this company.'))
        val_encabezado = {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            #'journal_id': journal_id.id,
            'currency_id': self.currency_id.id,
            'invoice_payment_term_id': self.payment_term_id.id,
            'company_id': company_id,
            'invoice_user_id': self.user_id and self.user_id.id,
            'invoice_line_ids': lineas,
        }

        account_move_id = obj_factura.create(val_encabezado)
        # account_move_id.action_post()
        self.write({
            'invoice_cxc_ids': [(6, 0, [account_move_id.id])],
            'state': 'aprobado'
        })
             
    def action_view_invoice(self):
        invoices = self.mapped('invoice_cxc_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view_id = self.env.ref('account.view_move_form').id
            action['views'] = [(form_view_id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        
        return action
            
       
    def action_view_payment(self):
        patment = self.mapped('payment_ids')
        action = self.env.ref('account.action_account_payments').read()[0]
        if len(patment) > 1:
            action['domain'] = [('id', 'in', patment.ids)]
        elif len(patment) == 1:
            action['views'] = [
                (self.env.ref('account.view_account_payment_form').id, 'form')]
            action['res_id'] = patment.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

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
            worksheet.write(row, 4, prestamo.meses_seleccion)
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
        
    