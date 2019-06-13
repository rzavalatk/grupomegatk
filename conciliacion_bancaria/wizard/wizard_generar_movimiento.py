# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning

class Wizardgenerarmovimiento(models.TransientModel):
    _name = "conciliacion.wizard.movimientos"
    _description = "Generar Movimientos"


    def _get_company(self):
        ctx = self._context
        if 'active_id' in ctx:
            obj_col = self.env["conicliacion.bancaria"].browse(ctx['active_id'])
            return obj_col.company_id

    def _get_account(self):
        ctx = self._context
        if 'active_id' in ctx:
            obj_col = self.env["conicliacion.bancaria"].browse(ctx['active_id'])
            return obj_col.account_id

    @api.onchange("journal_id")
    def onchangejournal(self):
        if self.journal_id:
            if self.journal_id.currency_id:
                self.currency_id = self.journal_id.currency_id.id
            else:
                self.currency_id = self.company_id.currency_id.id

    @api.one
    @api.depends('wizard_ids.amount', 'monto')
    def _compute_rest_credit(self):
        debit_line = 0
        credit_line = 0
        if self.doc_type == 'debit':
            for lines in self.wizard_ids:
                if lines.move_type == 'debit':
                    debit_line += lines.amount
                elif lines.move_type == 'credit':
                    credit_line += lines.amount
                else:
                    credit_line += 0
                    debit_line += 0
            self.total_debitos = debit_line
            self.total_creditos = credit_line
            self.rest_credit = self.monto - (debit_line - credit_line)
        else:
            for lines in self.wizard_ids:
                if lines.move_type == 'debit':
                    debit_line += lines.amount
                elif lines.move_type == 'credit':
                    credit_line += lines.amount
                else:
                    credit_line += 0
                    debit_line += 0
            self.total_debitos = debit_line
            self.total_creditos = credit_line
            self.rest_credit = round(self.monto - (credit_line - debit_line), 2)

    total_debitos = fields.Float("Total débitos", compute=_compute_rest_credit)
    total_creditos = fields.Float("Total créditos", compute=_compute_rest_credit)
    rest_credit = fields.Float('Diferencia', compute=_compute_rest_credit)

    company_id = fields.Many2one("res.company", "Empresa", default=_get_company, required=True)
    name = fields.Char("Descripción", required=True)
    journal_id = fields.Many2one("account.journal", "Diario", required=True)
    fecha = fields.Date("Fecha", required=True)
    monto = fields.Float("Monto")
    account_id = fields.Many2one('account.account', 'Cuenta', required=True, default=_get_account)
    doc_type = fields.Selection([('debit', 'Débito'), ('credit','Crédito')], string='Tipo', required=True)
    wizard_ids = fields.One2many("conciliacion.wizard.movimientos.line", "wizard_id", "Movimientos")
    currency_id = fields.Many2one("res.currency", "Moneda", domain=[('active', '=', True)])
    currency_rate = fields.Float("Tasa de Cambio", digits=(12, 6))
    es_moneda_base = fields.Boolean("Es moneda base")

    @api.onchange("currency_id")
    def onchangecurrency(self):
        if self.currency_id:
            if self.currency_id != self.company_id.currency_id:
                tasa = self.currency_id.with_context(date=self.fecha)
                self.currency_rate = 1 / tasa.rate 
                self.es_moneda_base = False
            else:
                self.currency_rate = 1
                self.es_moneda_base = True

    @api.multi
    def action_validate(self):
        if not self.wizard_ids:
            raise Warning(_("No existen detalles de movimientos a registrar"))
        if self.monto < 0:
            raise Warning(_("El total debe de ser mayor que cero"))
        if not round(self.rest_credit, 2) == 0.0:
            raise Warning(_("Existen diferencias entre el detalle y el total de la transacción a realizar"))

        self.write({'state': 'validated'})
        self.generate_asiento()


    def generate_asiento(self):
        account_move = self.env['account.move']
        lineas = []
        if self.doc_type == 'debit':
            vals_haber = {
                'debit': 0.0,
                'credit': self.monto * self.currency_rate,
                'name': self.name,
                'account_id': self.account_id.id,
                'date': self.fecha,
            }
            if self.journal_id.currency_id:
                if not self.company_id.currency_id == self.currency_id:
                    vals_haber["currency_id"] = self.currency_id.id
                    vals_haber["amount_currency"] = self.monto * -1
                else:
                    vals_haber["amount_currency"] = 0.0
            for line in self.wizard_ids:
                # LINEA DE DEBITO
                if line.move_type == 'debit':
                    vals_debe = {
                        'debit': line.amount * self.currency_rate,
                        'credit': 0.0,
                        'name': line.name or self.name,
                        'account_id': line.account_id.id,
                        'date': self.fecha,
                        'partner_id': line.partner_id.id,
                        'analytic_account_id': line.analytic_id.id,
                    }
                    if self.journal_id.currency_id:
                        if not self.company_id.currency_id == self.currency_id:
                            vals_debe["currency_id"] = self.currency_id.id
                            vals_debe["amount_currency"] = line.amount
                        else:
                            vals_debe["amount_currency"] = 0.0
                    lineas.append((0, 0, vals_debe))
                if line.move_type == 'credit':
                    vals_credit = {
                        'debit': 0.0,
                        'credit': line.amount * self.currency_rate,
                        'name': line.name or self.name,
                        'account_id': line.account_id.id,
                        'date': self.fecha,
                        'partner_id': line.partner_id.id,
                        'analytic_account_id': line.analytic_id.id,
                    }
                    if self.journal_id.currency_id:
                        if not self.company_id.currency_id == self.currency_id:
                            vals_credit["currency_id"] = self.currency_id.id
                            vals_credit["amount_currency"] = line.amount * -1
                        else:
                            vals_credit["amount_currency"] = 0.0
                    lineas.append((0, 0, vals_credit))
            lineas.append((0, 0, vals_haber))
        else:
            vals_credit = {
                'debit': self.monto * self.currency_rate,
                'credit': 0.0,
                'name': self.name,
                'account_id': self.account_id.id,
                'date': self.fecha,
            }
            if self.journal_id.currency_id:
                if not self.company_id.currency_id == self.currency_id:
                    vals_credit["currency_id"] = self.currency_id.id
                    vals_credit["amount_currency"] = self.monto
                else:
                    vals_credit["amount_currency"] = 0.0
            for line in self.wizard_ids:
                if line.move_type == 'credit':
                    vals_debe = {
                        'debit': 0.0,
                        'credit': line.amount * self.currency_rate,
                        'amount_currency': 0.0,
                        'name': line.name or self.name,
                        'account_id': line.account_id.id,
                        'date': self.fecha,
                        'partner_id': line.partner_id.id,
                        'analytic_account_id': line.analytic_id.id,
                    }
                    if self.journal_id.currency_id:
                        if not self.company_id.currency_id == self.currency_id:
                            vals_debe["currency_id"] = self.currency_id.id
                            vals_debe["amount_currency"] = line.amount
                        else:
                            vals_debe["amount_currency"] = 0.0
                    lineas.append((0, 0, vals_debe))
                if line.move_type == 'debit':
                    vals_credit = {
                        'debit': line.amount * self.currency_rate,
                        'credit': 0.0,
                        'amount_currency': 0.0,
                        'name': line.name or self.name,
                        'account_id': line.account_id.id,
                        'date': self.fecha,
                        'partner_id': line.partner_id.id,
                        'analytic_account_id': line.analytic_id.id,
                    }
                    if self.journal_id.currency_id:
                        if not self.company_id.currency_id == self.currency_id:
                            vals_credit["currency_id"] = self.currency_id.id
                            vals_credit["amount_currency"] = line.amount  * -1
                        else:
                            vals_credit["amount_currency"] = 0.0
                    lineas.append((0, 0, vals_credit))
            lineas.append((0, 0, vals_credit))
        values = {
            'journal_id': self.journal_id.id,
            'date': self.fecha,
            'ref': self.name,
            'line_ids': lineas,
            'state': 'posted',
        }
        id_move = account_move.create(values)
        if id_move:
            ctx = self._context
            obj_col = self.env["conicliacion.bancaria"].browse(ctx['active_id'])
            obj_move_id = self.env["account.move.line"].search([('account_id', '=', self.account_id.id), 
            ('company_id', '=', self.company_id.id), ('es_conciliado', '=', False), ('move_id', '=', id_move.id)], limit=1)
            obj_line = self.env["conicliacion.bancaria.line"]
            vals = {
                    'conciliacion_id': obj_col.id,
                    'move_id': id_move.id,
                    'move_line_id': obj_move_id.id,
                    'partner_id': obj_move_id.partner_id.id,
                    'date': id_move.date,
                    'currency_id': obj_move_id.currency_id.id,
                    'es_conciliado': False,
                    'name': obj_move_id.ref,
                    'importe_moneda': obj_move_id.amount_currency,
                }
            if obj_move_id.debit > 0:
                vals["debe"] = obj_move_id.debit
            if obj_move_id.credit > 0:
                vals["haber"] = obj_move_id.credit

            line_id =  obj_line.create(vals)


class Wizardgenerarmovimientoline(models.TransientModel):
    _name = "conciliacion.wizard.movimientos.line"

    @api.onchange("account_id")
    def onchangecuenta(self):
        if self.wizard_id.doc_type:
            if self.wizard_id.doc_type == 'credit':
               self.move_type = 'credit'
        else:
            self.move_type = ''


    wizard_id = fields.Many2one('conciliacion.wizard.movimientos', 'Wizard')
    partner_id = fields.Many2one('res.partner', 'Empresa')
    account_id = fields.Many2one('account.account', 'Cuenta', required=True)
    name = fields.Char('Descripción')
    amount = fields.Float('Monto')
    currency_id = fields.Many2one('res.currency', string='Currency')
    analytic_id = fields.Many2one("account.analytic.account", string="Cuenta Analitica")
    move_type = fields.Selection([('debit', 'Débito'), ('credit', 'Crédito')], 'Débito/Crédito', default='debit', required=True)