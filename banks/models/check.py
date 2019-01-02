# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from datetime import datetime
from odoo.exceptions import Warning


class Check(models.Model):
    _name = 'banks.check'
    _inherit = ['mail.thread']
    _order = 'date desc'

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
                n = seq.prefix + '%%0%sd' % seq.padding % (seq.number_next_actual + 1)
        for pay in payment_obj:
            pay.write({'name': n})
        for db in deb_obj:
            db.write({'number': n})

    @api.one
    def get_msg_number(self):
        if self.journal_id and self.state == 'draft':
            flag = False
            if not self.cheque_anulado:
                for seq in self.journal_id.secuencia_ids:
                    if seq.move_type == self.doc_type:
                        self.number_calc = seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual
                        flag = True
                    if not flag:
                        self.msg = "No existe numeración para este banco, verifique la configuración"
                        self.number_calc = ""
                    else:
                        self.msg = ""

    def get_char_seq(self, journal_id, doc_type):
        jr = self.env["account.journal"].search([('id', '=', journal_id)])
        for seq in jr.secuencia_ids:
            if seq.move_type == doc_type:
                return (seq.prefix + '%%0%sd' % seq.padding % seq.number_next_actual)

    journal_id = fields.Many2one("account.journal", "Banco", required=True)
    date = fields.Date(string="Fecha de Cheque ", required=True, default=fields.Date.context_today)
    total = fields.Float(string='Total', required=True)
    memo = fields.Text("Descripción", required=True)
    number = fields.Char("Número de cheque")
    anulation_date = fields.Date("Fecha de Anulación")
    sequence_id = fields.Many2one("ir.sequence", "Chequera")
    currency_id = fields.Many2one('res.currency', string='Moneda')
    name = fields.Char("Pagar a", required=True)
    check_lines = fields.One2many("banks.check.line", "check_id", "Detalle de cheques", required=True)
    state = fields.Selection([('draft', 'Borrador'), ('validated', 'Validado'), ('postdated', 'Post-Fechado'), ('anulated', 'Anulado')], string='Estado', readonly=True, default='draft')
    currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))
    difference = fields.Float(string='Diferencia', compute='_compute_rest_credit')
    doc_type = fields.Selection([('check', 'Cheque'), ('transference', 'Transferencia')], string='Tipo de Transacción', required=True)
    msg = fields.Char("Error de configuración", compute=get_msg_number)
    number_calc = fields.Char("Número de Transacción", compute=get_msg_number)
    move_id = fields.Many2one('account.move', 'Apunte Contable')
    company_id = fields.Many2one("res.company", "Empresa", default=lambda self: self.env.user.company_id, required=True)
    es_moneda_base = fields.Boolean("Es moneda base")
    plantilla_id = fields.Many2one("banks.template", "Plantilla")
    cheque_anulado = fields.Boolean("Cheque anulado")

    @api.onchange("plantilla_id")
    def onchangeplantilla(self):
        if self.plantilla_id:
            self.company_id = self.plantilla_id.company_id.id
            self.journal_id = self.plantilla_id.journal_id.id
            self.name = self.plantilla_id.pagar_a
            self.memo = self.plantilla_id.memo
            self.total = self.plantilla_id.total
            self.doc_type = self.plantilla_id.doc_type
            self.currency_id = self.plantilla_id.currency_id.id
            self.es_moneda_base = self.plantilla_id.es_moneda_base
            lineas = []
            for line in self.plantilla_id.detalle_lines:
                lineas.append((0, 0, {
                    'partner_id': line.partner_id.id,
                    'account_id': line.account_id.id,
                    'name': line.name,
                    'amount': line.amount,
                    'currency_id': line.currency_id.id,
                    'analytic_id': line.analytic_id.id,
                    'move_type': line.move_type,
                    'check_id': self.id,
                }))
            self.check_lines = lineas


    @api.model
    def create(self, vals):
        vals["number"] = self.get_char_seq(vals.get("journal_id"), vals.get("doc_type"))
        check = super(Check, self).create(vals)
        return check

    @api.multi
    def unlink(self):
        for move in self:
            if move.state == 'validated' or move.state == 'anulated':
                raise Warning(_('No puede eliminar registros contabilizados'))
        return super(Check, self).unlink()

    @api.one
    @api.depends('check_lines.amount', 'total')
    def _compute_rest_credit(self):
        debit_line = 0
        credit_line = 0
        for lines in self.check_lines:
            if lines.move_type == 'debit':
                debit_line += lines.amount
            elif lines.move_type == 'credit':
                credit_line += lines.amount
            else:
                credit_line += 0
                debit_line += 0
        self.difference = self.total - (debit_line - credit_line)


    @api.onchange("journal_id")
    def onchangejournal(self):
        self.get_msg_number()
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id.id
            else:
                self.currency_id = self.company_id.currency_id.id


    @api.multi
    def set_borrador(self):
        self.write({'state': 'draft'})

    @api.multi
    def action_anulate(self):
        self.write({'state': 'anulated'})
        self.cheque_anulado = True
        if not self.cheque_anulado:
            self.update_seq()
            self.number = self.env["ir.sequence"].search([('id', '=', self.get_sequence())]).next_by_id()

    @api.multi
    def action_anulate_cheque(self):
        for move in self.move_id:
            move.write({'state': 'draft'})
            move.unlink()
        self.write({'state': 'anulated'})
        self.cheque_anulado = True

    @api.multi
    def action_validate(self):
        if not self.cheque_anulado:
            if not self.number_calc:
                 raise Warning(_("El banco no cuenta con configuraciones/parametros para registrar cheques de terceros"))
        if not self.check_lines:
            raise Warning(_("No existen detalles de movimientos a registrar"))
        if self.total < 0:
            raise Warning(_("El total debe de ser mayor que cero"))
        if not round(self.difference, 2) == 0:
            raise Warning(_("Existen diferencias entre el detalle y el total de la transacción a realizar"))

        self.write({'state': 'validated'})
        if not self.cheque_anulado:
            self.number = self.env["ir.sequence"].search([('id', '=', self.get_sequence())]).next_by_id()
        self.write({'move_id': self.generate_asiento()})

    def generate_asiento(self):
        account_move = self.env['account.move']
        lineas = []
        vals_credit = {
            'debit': 0.0,
            'credit': self.total * self.currency_rate,
            'name': self.name,
            'account_id': self.journal_id.default_credit_account_id.id,
            'date': self.date,
            #'company_id': self.company_id.id,
        }
        if self.currency_id:
            if not self.company_id.currency_id == self.currency_id:
                vals_credit["currency_id"] = self.currency_id.id
                vals_credit["amount_currency"] = self.total * -1
            else:
                vals_credit["amount_currency"] = 0.0

        for line in self.check_lines:
            if line.move_type == 'debit':
                vals_debe = {
                    'debit': line.amount * self.currency_rate,
                    'credit': 0.0,
                    'name': line.name or self.name,
                    'account_id': line.account_id.id,
                    'date': self.date,
                    'partner_id': line.partner_id.id,
                    'analytic_account_id': line.analytic_id.id,
                }
                if self.currency_id:
                    if not self.company_id.currency_id == self.currency_id:
                        vals_debe["currency_id"] = self.currency_id.id
                        vals_debe["amount_currency"] = self.total
                    else:
                        vals_credit["amount_currency"] = 0.0
                lineas.append((0, 0, vals_debe))
            if line.move_type == 'credit':
                vals_credit_line = {
                    'debit': 0.0,
                    'credit': line.amount * self.currency_rate,
                    'name': line.name or self.name,
                    'account_id': line.account_id.id,
                    'date': self.date,
                    'partner_id': line.partner_id.id,
                    'analytic_account_id': line.analytic_id.id,
                }
                if self.currency_id:
                    if not self.company_id.currency_id == self.currency_id:
                        vals_credit_line["currency_id"] = self.currency_id.id
                        vals_credit_line["amount_currency"] = self.total * -1
                    else:
                        vals_credit["amount_currency"] = 0.0
                lineas.append((0, 0, vals_credit_line))
        lineas.append((0, 0, vals_credit))
        values = {
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': self.name,
            'line_ids': lineas,
            'state': 'posted',
        }
        id_move = account_move.create(values)
        id_move.write({'name': str(self.number)})
        return id_move.id


class check_line(models.Model):
    _name = 'banks.check.line'

    check_id = fields.Many2one('banks.check', 'Check')
    partner_id = fields.Many2one('res.partner', 'Empresa', domain="[('company_id', '=', parent.company_id)]")
    account_id = fields.Many2one('account.account', 'Cuenta', required=True)
    name = fields.Char('Descripción')
    amount = fields.Float('Monto', required=True)
    currency_id = fields.Many2one('res.currency', string='Moneda')
    analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica", domain="[('company_id', '=', parent.company_id)]")
    move_type = fields.Selection([('debit', 'Débito'), ('credit', 'Crédito')], 'Debit/Credit', default='debit', required=True)
