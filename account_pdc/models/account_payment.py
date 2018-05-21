# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.exceptions import Warning

class AccountPayment(models.Model):
    _name = "account.payment.invoices.custom"
    _order = 'effective_date asc'
    _inherit = ['mail.thread']

    def get_diferencia(self):
        if self.invoice_ids:
            line_amount = 0.0
            for linea in self.invoice_ids:
                line_amount += linea.monto_pago
            self.diferencia = self.amount - line_amount

    @api.onchange("currency_id")
    def onchangecurrency(self):
        if self.currency_id:
            if self.currency_id != self.company_id.currency_id:
                tasa = self.currency_id.with_context(date=self.date)
                self.currency_rate = 1 / tasa.rate
                self.es_moneda_base = False
            else:
                self.currency_rate = 1
                self.es_moneda_base = True

    @api.onchange("journal_id")
    def onchangejournal(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id.id
            else:
                self.currency_id = self.company_id.currency_id.id

    def get_name_seq_cliente(self):
        self.name = self.env['ir.sequence'].get('pago')

    bank_reference = fields.Char('Referencia de pago', required=True)
    journal_id = fields.Many2one("account.journal", "Banco", required=True, states={'draft': [('readonly', False)]}, domain=[('type', '=', 'bank')])
    effective_date = fields.Date('Fecha efectiva', help='Fecha del deposito del cheque', required=True, states={'draft': [('readonly', False)]})
    invoice_ids = fields.One2many('account.payment.line.custom', 'pago_id', string="Facturas", readonly=False, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one("res.partner", "Cliente", required=True, states={'draft': [('readonly', False)]})
    amount = fields.Float("Monto a pagar", required=True, states={'draft': [('readonly', False)]})
    date = fields.Date("Fecha de registro", required=True, states={'draft': [('readonly', False)]})
    name = fields.Char("Referencia", default= "/")
    move_id = fields.Many2one('account.move', 'Asiento Contable', ondelete='restrict', readonly=True)
    state = fields.Selection([('draft', 'Borrador'), ('paid', 'Pagado'), ('cancel', 'Cancelado')], string='Estado', index=True, readonly=True, default='draft')
    notes = fields.Text("Notas")
    diferencia = fields.Float("Diferencia", compute=get_diferencia)
    currency_id = fields.Many2one('res.currency', string='Moneda')
    company_id = fields.Many2one("res.company", "Empresa", required=True)
    es_moneda_base = fields.Boolean("Es moneda base")
    currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))

    @api.multi
    def get_invoices(self):
        invoice_ids = self.env["account.invoice"].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'open'), 
            ('currency_id', '=', self.currency_id.id), ('type','=','out_invoice')])
        facturas = self.env["account.payment.line.custom"]
        if not invoice_ids:
            raise Warning(_('No existen facturas para este cliente'))
        dict_invoices = {}
        self.invoice_ids.unlink()
        for invoice in invoice_ids:
            vals = {
                'pago_id': self.id,
                'partner_id': self.partner_id.id,
                'number': invoice.number,
                'date_invoice': invoice.date_invoice,
                'date_due': invoice.date_due,
                'name': invoice.name,
                'invoice_id': invoice.id,
                'amount_total': invoice.amount_total,
                'residual': invoice.residual,
                'state': invoice.state,
            }
            facturas.create(vals)

    @api.multi
    def post_payment(self):
        if self.amount <= 0:
            raise Warning(_('El monto debe de ser mayor que cero'))
        if not self.invoice_ids:
            raise Warning(_('No existen facturas para registrar pagos'))
        total_line = 0
        for linea in self.invoice_ids:
            total_line += linea.monto_pago
        if not round(total_line, 2) == round(self.amount, 2):
            raise Warning(_('Existen diferencias, verifique el monto de las facturas'))
        account_move = self.env['account.move']
        lineas = []
        to_reconcile_ids = {}
        to_reconcile_lines = self.env['account.move.line']
        for factura in self.invoice_ids:
            if factura.currency_id != self.currency_id:
                 raise Warning(_('Esta tratando de pagar con monedas diferentes, favor verifique la moneda de pago sean igual que el de las facturas'))
            if factura.monto_pago > 0:
                vals_interes = {
                    'debit': 0.0,
                    'credit': factura.monto_pago * self.currency_rate,
                    'name': 'Pago de Factura',
                    'account_id': self.partner_id.property_account_receivable_id.id,
                    'partner_id': self.partner_id.id,
                    'date': self.effective_date,
                    'invoice_id': factura.invoice_id.id,
                }
                if self.journal_id.currency_id:
                    vals_interes["currency_id"] = self.currency_id.id
                    vals_interes["amount_currency"] = factura.monto_pago 
                lineas.append((0, 0, vals_interes))
                movelines = factura.invoice_id.move_id.line_ids
                for line in movelines:
                    if line.account_id.id == factura.invoice_id.account_id.id:
                        to_reconcile_lines += line
        vals_banco = {
                'debit': self.amount * self.currency_rate,
                'credit': 0.0,
                'amount_currency': 0.0,
                'name': 'Pago de prestamo',
                'account_id': self.journal_id.default_debit_account_id.id,
                'partner_id': self.partner_id.id,
                'date': self.effective_date,
                'invoice_id': factura.invoice_id.id,
        }
        if self.journal_id.currency_id:
            vals_interes["currency_id"] = self.currency_id.id
            vals_interes["amount_currency"] = self.amount * -1
        lineas.append((0, 0, vals_banco))
        values = {
            'journal_id': self.journal_id.id,
            'date': self.effective_date,
            'ref': 'Pago de facturas',
            'line_ids': lineas,
        }
        id_move = account_move.create(values)
        if id_move:
            for invs in self.invoice_ids:
                if invs.monto_pago > 0:
                    self.reconciliar(invs.invoice_id.id, id_move.id)
            self.write({'move_id': id_move.id, 'state': 'paid'})

        self.get_name_seq_cliente()

    def reconciliar(self, invoice_id, move_id):
        to_reconcile_lines = self.env['account.move.line']
        inv = self.env["account.invoice"].search([('id', '=', invoice_id)])
        account_move = self.env['account.move'].search([('id', '=', move_id)])
        movelines = inv.move_id.line_ids
        for line in movelines:
            if line.account_id.id == inv.account_id.id:
                to_reconcile_lines += line

        for tmpline in account_move.line_ids:
            if tmpline.account_id.id == inv.account_id.id and tmpline.invoice_id.id == inv.id:
                to_reconcile_lines += tmpline
                to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()


class Payemtline(models.Model):
    _name = "account.payment.line.custom"

    pago_id = fields.Many2one("account.payment.invoices.custom", "Pago")
    partner_id = fields.Many2one("res.partner", "Cliente")
    number = fields.Char("Número de factura")
    date_invoice = fields.Date('Fecha de factura')
    date_due = fields.Date('Fecha de vencimiento')
    name = fields.Char("Referencia")
    invoice_id = fields.Many2one('account.invoice', string="Invoices", readonly=False)
    amount_total = fields.Float("Total de factura")
    residual = fields.Float("Saldo de pendiente")
    monto_pago = fields.Float("Monto a pagar")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('proforma', 'Pro-forma'),
            ('proforma2', 'Pro-forma'),
            ('open', 'Open'),
            ('paid', 'Paid'),
            ('cancel', 'Cancelled'),
        ], string='Status', index=True, readonly=True, default='draft')
    currency_id = fields.Many2one('res.currency', string='Moneda', related="invoice_id.currency_id")
    
    @api.onchange("monto_pago")
    def validated_amount(self):
        if self.monto_pago > self.residual:
            raise Warning(_('El monto ingresado es mayor que el saldo de la factura'))
