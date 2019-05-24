# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.exceptions import Warning


class BanksPayment(models.Model):
    _name = "banks.payment.invoices.custom"
    _order = 'effective_date asc'
    _inherit = ['mail.thread']

    def get_sequence(self):
        if self.journal_id:
            for seq in self.journal_id.secuencia_ids:
                if seq.move_type == self.doc_type:
                    return seq.id


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

    def update_seq(self):
        deb_obj = self.env["banks.check"].search([('state', '=', 'draft'), ('doc_type', '=', self.doc_type)])
        payment_obj = self.env["banks.payment.invoices.custom"].search([('state', '=', 'draft'), ('doc_type', '=', self.doc_type)])
        n = ""
        for seq in self.journal_id.secuencia_ids:
            if seq.move_type == self.doc_type:
                n = seq.prefix + '%%0%sd' % seq.padding % (seq.number_next_actual)
        for db in deb_obj:
            db.write({'number': n})
        for pay in payment_obj:
            pay.write({'name': n})

    def get_char_seq(self, journal_id, doc_type):
        jr = self.env["account.journal"].search([('id', '=', journal_id)])
        for seq in jr.secuencia_ids:
            if seq.move_type == doc_type:
                return (seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual)

    @api.one
    @api.depends('invoice_ids.monto_pago', 'amount')
    def get_diferencia(self):
        if self.invoice_ids:
            line_amount = 0.0
            for linea in self.invoice_ids:
                line_amount += linea.monto_pago
            self.diferencia = self.amount - line_amount

    def get_msg_number(self):
        if self.journal_id and self.state == 'draft':
            flag = False
            for seq in self.journal_id.secuencia_ids:
                if seq.move_type == self.doc_type:
                    self.name = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
                    flag = True
            if not flag:
                self.msg = "No existe numeración para este banco, verifique la configuración"
                self.name = ""
            else:
                self.msg = ""

    bank_reference = fields.Char('Referencia de pago', required=True)
    journal_id = fields.Many2one("account.journal", "Banco/Efectivo", required=True, states={'draft': [('readonly', False)]})
    effective_date = fields.Date('Fecha efectiva', help='Fecha del deposito del cheque', states={'draft': [('readonly', False)]})
    invoice_ids = fields.One2many('banks.payment.line.custom', 'pago_id', string="Facturas", readonly=False, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one("res.partner", "Proveedor", required=True, domain=[('supplier', '=', True)], states={'draft': [('readonly', False)]})
    amount = fields.Float("Monto a pagar", required=True, states={'draft': [('readonly', False)]})
    date = fields.Date("Fecha de registro", required=True, states={'draft': [('readonly', False)]})
    name = fields.Char("Número")
    move_id = fields.Many2one('account.move', 'Asiento Contable', ondelete='restrict', readonly=True)
    state = fields.Selection([('draft', 'Borrador'), ('paid', 'Pagado'), ('cancel', 'Cancelado')], string='Estado', index=True, readonly=True, default='draft')
    notes = fields.Text("Notas")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    diferencia = fields.Float("Diferencia", compute=get_diferencia)
    doc_type = fields.Selection([('check', 'Cheque'), ('transference', 'Transferencia'), ('otro', 'Otro')], string='Tipo de Transacción', required=True)
    msg = fields.Char("Error de configuración", compute=get_msg_number)
    company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.user.company_id, required=True)
    es_moneda_base = fields.Boolean("Es moneda base")
    currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))

    @api.onchange("doc_type")
    def onchangedoc_type(self):
        if self.journal_id and self.doc_type:
            self.get_msg_number()

    @api.onchange("journal_id")
    def onchangejournal(self):
        self.get_msg_number()
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id.id
            else:
                self.currency_id = self.company_id.currency_id.id

    @api.model
    def create(self, vals):
        vals["name"] = self.get_char_seq(vals.get("journal_id"), vals.get("doc_type"))
        check = super(BanksPayment, self).create(vals)
        return check

    @api.multi
    def get_invoices(self):
        invoice_ids = self.env["account.invoice"].search([('partner_id', '=', self.partner_id.id), ('state', '=', 'open'), 
            ('currency_id', '=', self.currency_id.id), ('type','=','in_invoice')])
        facturas = self.env["banks.payment.line.custom"]
        if not invoice_ids:
            raise Warning(_('No existen facturas para este cliente'))
        dict_invoices = {}
        self.invoice_ids.unlink()
        for invoice in invoice_ids:
            vals = {
                'pago_id': self.id,
                'partner_id': self.partner_id.id,
                'number': invoice.numero_factura,
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
                    'debit': factura.monto_pago * self.currency_rate,
                    'credit': 0.0,
                    'name': 'Pago de Factura',
                    'account_id': self.partner_id.property_account_payable_id.id,
                    'partner_id': self.partner_id.id,
                    'date': self.effective_date or self.date,
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
                'debit': 0.0,
                'credit': self.amount * self.currency_rate,
                'name': 'Pago de prestamo',
                'account_id': self.journal_id.default_credit_account_id.id,
                'partner_id': self.partner_id.id,
                'date': self.effective_date or self.date,
                'invoice_id': factura.invoice_id.id,
        }
        if self.journal_id.currency_id:
            vals_banco["currency_id"] = self.currency_id.id
            vals_banco["amount_currency"] = self.amount * -1
        lineas.append((0, 0, vals_banco))
        values = {
            'journal_id': self.journal_id.id,
            'date': self.effective_date or self.date,
            'ref': 'Pago de facturas',
            'line_ids': lineas,
            'state': 'posted',
        }
        id_move = account_move.create(values)
        id_move.write({'name': str(self.name)})
        if id_move:
            for invs in self.invoice_ids:
                if invs.monto_pago > 0:
                    self.reconciliar(invs.invoice_id.id, id_move.id)
            self.write({'move_id': id_move.id, 'state': 'paid'})

        self.number = self.env["ir.sequence"].search([('id', '=', self.get_sequence())]).next_by_id()
        self.update_seq()


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


class BanksPayemtline(models.Model):
    _name = "banks.payment.line.custom"

    pago_id = fields.Many2one("banks.payment.invoices.custom", "Pago")
    partner_id = fields.Many2one("res.partner", "Proveedor")
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
