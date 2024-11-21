# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanRequest(models.Model):
    """Puede crear nuevas solicitudes de préstamo y administrar registros."""
    _name = 'loan.request'
    _inherit = ['mail.thread']
    _description = 'Loan Request'
    
    # ºººººº METODOS COMPUTADOS ººººººººººººº
    @api.depends('date_init', 'meses_seleccion')
    def _compute_date_ends(self):
        for record in self:
            if record.date_init and record.meses_seleccion:
                meses = int(record.meses_seleccion)
                record.date_ends = record.date_init + relativedelta(months=meses)
            else:
                record.date_ends = False
    
    def _compute_invoiced(self):
        for prestamo in self:
            prestamo.invoice_count_cxc = len(prestamo.invoice_cxc_ids)
            prestamo.payment_count = len(prestamo.payment_ids)
            prestamo.cuotas_count = len(prestamo.repayment_lines_ids)
    

    #DATOS GENERALES
    name = fields.Char(string='Número de Préstamo', copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, readonly=True, states={'borrador': [('readonly', False)]}, copy=False)
    remaining_capital = fields.Monetary('Capital restante', readonly=True,  copy=False, )
    pay_capital = fields.Monetary('Capital pagado',  readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    note = fields.Text('Notas', readonly=True, states={'borrador': [('readonly', False)]}, copy=False) #Agregar a un campo en una page del notebook
    processing_fee = fields.Integer(string="Prima de procesamiento",  help="Importe para inicializar el préstamo")
    
    #Datos del prestamo 
    amount_borrowed = fields.Monetary(string='Monto del Préstamo', store=True, readonly=True, states={'borrador': [('readonly', False)]},)
    cuota = fields.Monetary('Cuota', readonly=True,  copy=False,)
    loan_type_id = fields.Many2one('loan.type', string='Prestamo', required=True)
    documents_ids = fields.Many2many('loan.documents', string="Documentos",)
    img_attachment_ids = fields.Many2many('ir.attachment', relation="m2m_ir_identity_card_rel",column1="documents_ids",string="Imagenes",)
    reject_reason = fields.Text(string="Razon de rechazo")
    request = fields.Boolean(string="Request", default=False)
    
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
    sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
    
    #Datos de contabilidad
    payment_term_id = fields.Many2one('account.payment.term', string='Plazo de pago',required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    interest_rate = fields.Float(string='Tasa de Interés', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
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
        ('1', 'Anual'),
    ], string='Frecuencia de Pago', default='12', required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    loan_type = fields.Selection([
        ('personal', 'Personal'),
        ('financiamiento', 'Financiamiento')
    ], string='Tipo de Préstamo', default="personal", required=True, readonly=True, states={'borrador': [('readonly', False)]},)
    
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('aprobado', 'Aprobado'),
        ('pro_pago', 'Proceso de pago'),
        ('rechazado', 'Rechazado'),
        ('cancelado', 'Cancelado'),
        ('pagado', 'Pagado'),
    ], string='Estado', default='borrador',  required=True, readonly=True, copy=False,
        tracking=True,)
       
    
    repayment_lines_ids = fields.One2many('repayment.line',
                                          'loan_id',
                                          string="Cuotas", index=True,)

   
    # ||||||||||||| METODOS CRUD DEL PRESTAMO ||||||||||||||||
    
    @api.model
    def create(self, vals):
        """verifica si el cliente tiene un prestamo en procesop de pago sino crear una secuencia automática para los registros de solicitudes de préstamo"""
        loan_count = self.env['loan.request'].search(
            [('partner_id', '=', vals['partner_id']),
             ('state', 'not in', ('borrador', 'rechazado', 'cancelado'))])
        if loan_count:
            for rec in loan_count:
                if rec.state != 'pagado':
                    raise UserError(
                        _('El socio ya tiene un préstamo en curso.'))
        else:
            res = super().create(vals)
            return res
    
    def unlink(self):
        for prestamo in self:
            if prestamo.state != 'borrador':
                raise UserError(_('No se puede eliminar o cancelar una prestamo en estado ' + prestamo.state))
        return super(LoanRequest, self).unlink()
    
    # ||||||||||||||| METODOS ONCHANGE ||||||||||||||||||||

    @api.onchange('loan_type_id')
    def _onchange_loan_type_id(self):
        """Cambia los valores dependiendo el tipo de prestamo que elegimos"""
        type_id = self.loan_type_id
        self.amount_borrowed = type_id.disbursal_amount
        self.processing_fee = type_id.processing_fee
        self.meses_seleccion = type_id.meses_seleccion
        self.interest_rate = type_id.interest_rate * 100
        self.documents_ids = type_id.documents_ids
        
    @api.onchange('remaining_capital')
    def _onchange_pay_capital(self):
        for loan in self:
            loan.pay_capital = loan.amount_borrowed - loan.remaining_capital

    def go_to_draft(self):
        for prestamo in self:
            prestamo.state = 'borrador'
    
    # ºººººº ACCIONES DE BOTONES ºººººººººººº
    def action_loan_request(self):
        """Cambia el estado a confirmado y manda el correo de notificacion al cliente"""
        
        if not self.name:
            if self.loan_type == 'personal':
                obj_sequence = self.env["ir.sequence"].search(
                    [('company_id', '=', self.company_id.id), ('name', '=', 'Prestamo personal')])
                if not obj_sequence.id:
                    values = {'name': 'Prestamo personal',
                            'prefix': 'PRSTMO. ',
                            'company_id': self.company_id.id,
                            'padding': 6, }
                    sequence_id = obj_sequence.create(values)
                else:
                    sequence_id = obj_sequence
                self.write({'sequence_id': sequence_id.id})
            else:
                obj_sequence = self.env["ir.sequence"].search(
                [('company_id', '=', self.company_id.id), ('name', '=', 'Financiamiento')])
                if not obj_sequence.id:
                    values = {'name': 'Prestamo financiamiento',
                            'prefix': 'FINAN. ',
                            'company_id': self.company_id.id,
                            'padding': 6, }
                    sequence_id = obj_sequence.create(values)
                else:
                    sequence_id = obj_sequence
                self.write({'sequence_id': sequence_id.id})

            new_name = self.sequence_id.with_context().next_by_id()
            self.write({'name': new_name})
        else:
            self.write({'sequence_id': self.sequence_id.id})
            new_name = self.sequence_id.with_context().next_by_id()
            self.write({'name': new_name})
        
        
        self.write({'state': "confirmado"})
        partner = self.partner_id
        loan_no = self.name
        subject = 'Prestamo confirmado'

        message = (f"Estimado/a {partner.name},<br/> este es un correo notificando" 
                   f"la confirmación de su prestamo con numero {loan_no}." 
                   f"Hemos enviado su préstamo para aprobación, se le estara notificando")
        outgoing_mail = self.company_id.email
        mail_values = {
            'subject': subject,
            'email_from': outgoing_mail,
            'author_id': self.env.user.partner_id.id,
            'email_to': partner.email,
            'body_html': message,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()

    def action_approve(self):
        self.crear_factura()
        self.write({'state': "pro_pago"})
        partner = self.partner_id
        loan_no = self.name
        subject = 'Prestamo Aprobado'

        message = (f"Estimado/a {partner.name},<br/> este es un correo notificando" 
                   f"la aprobación de su prestamo con numero {loan_no}.<br/>" 
                   f"Se le genero una cuota mensual con un saldo de {self.cuota}.<br/>"
                   f"Para mas información contactar con servicio al cliente.")
        outgoing_mail = self.company_id.email
        mail_values = {
            'subject': subject,
            'email_from': outgoing_mail,
            'author_id': self.env.user.partner_id.id,
            'email_to': partner.email,
            'body_html': message,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
        
    def action_reject(self):
        self.write({'state': "rechazado"})
        partner = self.partner_id
        loan_no = self.name
        subject = 'Prestamo Rechazado'

        message = (f"Estimado/a {partner.name},<br/> este es un correo notificando" 
                   f" que su prestamo con numero {loan_no} fue rechazado.<br/>"
                   f"Para mas información contactar con servicio al cliente.")
        outgoing_mail = self.company_id.email
        mail_values = {
            'subject': subject,
            'email_from': outgoing_mail,
            'author_id': self.env.user.partner_id.id,
            'email_to': partner.email,
            'body_html': message,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
        
    def action_cancel(self):
        cuotas = self.env["repayment.line"].search(
            [('loan_id', '=', self.id)])
        if cuotas:
            for cuota in cuotas:
                if cuota.state != 'unpaid':
                    raise UserError(_('No se puede eliminar o cancelar un prestamo en estado de ' + self.state))
                cuota.sudo().unlink()         

        self.write({'state': 'cancelado',
                    'cuota': 0
                    })
        
    def ending(self):
        """Cerrar prestamo"""
        demo = []
        for check in self.repayment_lines_ids:
            if check.state == 'unpaid':
                demo.append(check)
        if len(demo) >= 1:
            message_id = self.env['message.popup'].create(
                {'message': _("Pagos pendientes")})
            return {
                'name': _('Repayment'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.popup',
                'res_id': message_id.id,
                'target': 'new'
            }
        self.write({'state': "pagado"})
    
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

    # ººººººº METODOS DE FUNCIONAMIENTO ººººººººººº
    
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
    
    def action_compute_repayment(self):
        """Esto crea automáticamente la cuota que el empleado necesita pagar a
            empresa en función de la fecha de inicio del pago y el número de plazos.
            """
        self.request = True
        partner = self.partner_id
        for prestamo in self:
            prestamo.repayment_lines_ids.unlink()
            if prestamo.interest_rate > 0:
                if prestamo.amount_borrowed <= 0:
                    raise UserError(_("No se puede procesar el prestamo, monto menor que cero o es cero."))
                else:
                    time.sleep(2)
                    cuota_obj = self.env['repayment.line']
                    
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
                            'loan_id': prestamo.id,
                            'partner_id': partner.id,
                            'amount': cuota_mensual,
                            'amount_capital_quota': capital_amortizado,
                            'amount_capital_loan': saldo_pendiente,
                            'interest_rate': prestamo.interest_rate,
                            'interest_generated': interes,
                            'recibir_pagos': prestamo.recibir_pagos.id,
                            'interest_account_id': prestamo.account_id.id,
                            'date_due': self.date_due_cuota(prestamo.date_init, total_payments, payments_per_year, n),
                        })
                        
                        if n <= total_payments:
                            n = n + 1
                    
            else:
                 raise UserError(_("La tasa no puede ser menor que cero"))
    
    def crear_pago_capital(self, monto):
        self.request = True
        
        invoices = self.mapped('invoice_cxc_ids')
        capital_invoice = invoices[0]
        
        payment = self.env['account.payment'].create({
            'payment_type': 'inbound',  # o 'outbound' dependiendo del tipo de pago, este es para recibir dineros
            'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
            'partner_type': 'customer',
            'ref': f'Pago a capital de ' + capital_invoice.name,
            'partner_id': capital_invoice.partner_id.id,
            'amount': monto,  # reemplaza con el monto del pago
            'currency_id': capital_invoice.currency_id.id,
            'reconciled_invoice_ids': [(4, capital_invoice.id)],
            #'account_id': capital_invoice.partner_id.property_account_payable_id.id,  # configuramos la cuenta por pagar
        })

        # Registramos el pago
        payment.action_post()
    
               
    def re_write_cuotas(self, monto, date,res_pago=True):
        self.request = True
        partner = self.partner_id
        cuotas_no_pagadas = 0
        for prestamo in self:
            
            prestamo.crear_pago_capital(monto)
            prestamo.remaining_capital = prestamo.remaining_capital - monto
            prestamo.pay_capital = prestamo.pay_capital + monto
            
            for cuota in prestamo.repayment_lines_ids:
                if cuota.state == 'unpaid':
                    cuotas_no_pagadas = cuotas_no_pagadas + 1
                    cuota.unlink()
            
            if prestamo.interest_rate > 0:
                if prestamo.remaining_capital <= 0:
                    raise UserError(_("No se puede procesar el prestamo, monto menor que cero o es cero."))
                else:
                    time.sleep(2)
                    cuota_obj = self.env['repayment.line']
                    
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
                    
                    saldo_pendiente = prestamo.remaining_capital
                    tasa_interes_mensual = prestamo.interest_rate / 100 / 12
                    amortizacion_constante = prestamo.amount_borrowed / total_payments
                    
                    # Calcular la cuota fija mensual
                    cuota_mensual = prestamo.cuota
                    
                    n = 1
                    interes = 0
                    capital_amortizado = 0

                    time.sleep(2)
                    for cuota_number in range((int(total_payments)-cuotas_no_pagadas), int(total_payments) + 1):
                        
                        
                        if saldo_pendiente > 0 and saldo_pendiente < cuota_mensual:
                            interes = 0
                            capital_amortizado = saldo_pendiente
                            saldo_pendiente = 0
                        elif saldo_pendiente <= 0:
                            capital_amortizado = 0
                            interes = 0
                            saldo_pendiente = 0
                        else:
                            interes = saldo_pendiente * tasa_interes_mensual
                            capital_amortizado = cuota_mensual - interes
                            saldo_pendiente -= capital_amortizado
                            
                        cuota_obj.create({
                            'name': f'Cuota {cuota_number}/{total_payments} de {prestamo.name}',
                            'loan_id': prestamo.id,
                            'partner_id': partner.id,
                            'amount': cuota_mensual,
                            'amount_capital_quota': capital_amortizado,
                            'amount_capital_loan': saldo_pendiente,
                            'interest_rate': prestamo.interest_rate,
                            'interest_generated': interes,
                            'recibir_pagos': prestamo.recibir_pagos.id,
                            'interest_account_id': prestamo.account_id.id,
                            'date_due': self.date_due_cuota(prestamo.date_init, total_payments, payments_per_year, n),
                        })
                    
                        
                        if n <= total_payments:
                            n = n + 1
                    
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
            'account_id': self.env["account.account"].browse(6751).id,
            'price_unit': self.amount_borrowed,
            'quantity': 1,
            'product_id': False,
            'x_user_id': self.env.user.id
        }
        lineas.append((0, 0, val_lineas))
        """if self.gasto_prestamo > 0:
            val_lineas1 = {
                'name': 'Cargos administrativos',
                'account_id': self.account_gasto_id.id,
                'price_unit': self.gasto_prestamo,
                'quantity': 1,
                'product_id': False,
                'x_user_id': self.env.user.id
            }
            lineas.append((0, 0, val_lineas1))"""
        company_id = self.company_id.id
        journal_id = self.recibir_pagos
        if not journal_id:
            raise UserError(
                _('Defina un diario contable de ventas para esta empresa.'))
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
