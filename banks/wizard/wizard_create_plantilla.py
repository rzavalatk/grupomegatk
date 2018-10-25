# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class WizardTemplatebanks(models.TransientModel):
    _name = "banks.wizard.template"

    name = fields.Char("Nombre de plantilla", required=True)

    @api.multi
    def set_template(self):
        obj_template = self.env["banks.template"]
        ctx = self._context
        banks_context = self.env[ctx["active_model"]].browse(ctx['active_id'])
        for obj_banks in banks_context:
            lineas = []
            if obj_banks.doc_type == 'check' or  obj_banks.doc_type == 'transference':
                for obj_banks_line  in obj_banks.check_lines:
                    vals_linea = {
                        'partner_id': obj_banks_line.partner_id.id,
                        'account_id': obj_banks_line.account_id.id,
                        'name': obj_banks_line.name,
                        'amount': obj_banks_line.amount,
                        'currency_id': obj_banks_line.currency_id.id,
                        'analytic_id': obj_banks_line.analytic_id.id,
                        'move_type': obj_banks_line.move_type,
                    }
                    lineas.append((0, 0, vals_linea))
            if obj_banks.doc_type == 'debit' or  obj_banks.doc_type == 'credit' or obj_banks.doc_type == 'deposit':
                for obj_banks_line  in obj_banks.debit_line:
                    vals_linea = {
                        'partner_id': obj_banks_line.partner_id.id,
                        'account_id': obj_banks_line.account_id.id,
                        'name': obj_banks_line.name,
                        'amount': obj_banks_line.amount,
                        'currency_id': obj_banks_line.currency_id.id,
                        'analytic_id': obj_banks_line.analytic_id.id,
                        'move_type': obj_banks_line.move_type,
                    }
                    lineas.append((0, 0, vals_linea))

            vals_template = {
                'name': self.name,
                'pagar_a': obj_banks.name,
                'journal_id': obj_banks.journal_id.id,
                'total': obj_banks.total,
                'currency_id': obj_banks.currency_id.id,
                'currency_rate': obj_banks.currency_rate,
                'doc_type': obj_banks.doc_type,
                'es_moneda_base': obj_banks.es_moneda_base,
                'detalle_lines': lineas,
            }
            if obj_banks.doc_type == 'check' or  obj_banks.doc_type == 'transference':
                vals_template["memo"] = obj_banks.memo
            obj_template.create(vals_template)