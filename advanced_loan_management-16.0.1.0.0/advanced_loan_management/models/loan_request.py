# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import date
import time
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class LoanRequest(models.Model):
    """Can create new loan requests and manage records"""
    _name = 'loan.request'
    _inherit = ['mail.thread']
    _description = 'Loan Request'

    #DATOS GENERALES
    name = fields.Char(string='Número de Préstamo', required=True, copy=False, readonly=True, default='Nuevo')
    partner_id = fields.Many2one('res.partner', string="Cliente", required=True, readonly=True, states={'borrador': [('readonly', False)]}, copy=False)
    remaining_capital = fields.Monetary('Capital restante', readonly=True,  copy=False, )
    pay_capital = fields.Monetary('Capital pagado',  readonly=True, states={'borrador': [('readonly', False)]}, copy=False,)
    note = fields.Text('Notas', readonly=True, states={'borrador': [('readonly', False)]}, copy=False) #Agregar a un campo en una page del notebook
    disbursal_amount = fields.Float(string="Disbursal_amount", help="Total loan amount available to disburse")
    
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

   
    @api.model
    def create(self, vals):
        """create  auto sequence for the loan request records"""
        loan_count = self.env['loan.request'].search(
            [('partner_id', '=', vals['partner_id']),
             ('state', 'not in', ('draft', 'rejected', 'closed'))])
        if loan_count:
            for rec in loan_count:
                if rec.state != 'closed':
                    raise UserError(
                        _('The partner has already an ongoing loan.'))
        else:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'increment_loan_ref')
            res = super().create(vals)
            return res

    @api.onchange('loan_type_id')
    def _onchange_loan_type_id(self):
        """Changing field values based on the chosen loan type"""
        type_id = self.loan_type_id
        self.amount_borrowed = type_id.loan_amount
        self.disbursal_amount = type_id.disbursal_amount
        self.meses_seleccion = type_id.meses_seleccion
        self.interest_rate = type_id.interest_rate
        self.documents_ids = type_id.documents_ids

    
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
        
    def go_to_draft(self):
        for prestamo in self:
            prestamo.state = 'borrador'
    
    def action_loan_request(self):
        """Cambia el estado a confirmado y manda el correo de notificacion al cliente"""
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
        self.write({'state': "aprobado"})
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

    """def action_disburse_loan(self):
       
        self.write({'state': "disbursed"})

        for loan in self:
            amount = loan.disbursal_amount
            loan_name = loan.partner_id.name
            reference = loan.name
            journal_id = loan.journal_id.id
            debit_account_id = loan.debit_account_id.id
            credit_account_id = loan.credit_account_id.id
            date_now = loan.date
            debit_vals = {
                'name': loan_name,
                'account_id': debit_account_id,
                'journal_id': journal_id,
                'date': date_now,
                'debit': amount > 0.0 and amount or 0.0,
                'credit': amount < 0.0 and -amount or 0.0,

            }
            credit_vals = {
                'name': loan_name,
                'account_id': credit_account_id,
                'journal_id': journal_id,
                'date': date_now,
                'debit': amount < 0.0 and -amount or 0.0,
                'credit': amount > 0.0 and amount or 0.0,
            }
            vals = {
                'name': f'DIS / {reference}',
                'narration': reference,
                'ref': reference,
                'journal_id': journal_id,
                'date': date_now,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            move = self.env['account.move'].create(vals)
            move.action_post()
        return True"""

    def action_close_loan(self):
        """Closing the loan"""
        demo = []
        for check in self.repayment_lines_ids:
            if check.state == 'unpaid':
                demo.append(check)
        if len(demo) >= 1:
            message_id = self.env['message.popup'].create(
                {'message': _("Pending Repayments")})
            return {
                'name': _('Repayment'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'message.popup',
                'res_id': message_id.id,
                'target': 'new'
            }
        self.write({'state': "closed"})

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

    def action_compute_repayment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        self.request = True
        for loan in self:
            loan.repayment_lines_ids.unlink()
            date_start = (datetime.strptime(str(loan.date),
                                            '%Y-%m-%d') +
                          relativedelta(months=1))
            amount = loan.amount_borrowed / loan.tenure
            interest = loan.amount_borrowed * loan.interest_rate
            interest_amount = interest / loan.tenure
            total_amount = amount + interest_amount
            partner = self.partner_id
            for rand_num in range(1, loan.tenure + 1):
                self.env['repayment.line'].create({
                    'name': f"{loan.name}/{rand_num}",
                    'partner_id': partner.id,
                    'date': date_start,
                    'amount': amount,
                    'interest_amount': interest_amount,
                    'total_amount': total_amount,
                    'loan_id': loan.id})
                date_start += relativedelta(months=1)
        return True
