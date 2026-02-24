# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SequenceJournal(models.TransientModel):
    _name = "sar.journal.settings"
    _description = "Journal Settings"

    def _get_company(self):
        contexto = self._context
        print ("*" * 200)
        if 'active_id' in contexto:
            print ("*" * 200)
            obj_fiscal = self.env["sar.authorization.code"].browse(contexto['active_id'])
            obj_company =  self.env["res.company"].search([('id', '=', obj_fiscal.company_id.id)]) 
            print (obj_company)
            print ("*" * 200)
            return obj_company


    company_id = fields.Many2one('res.company', "Empresa", deafult=_get_company)
    journal_id = fields.Many2one("account.journal", "Diario", required=True)
    vitt_prefix = fields.Char('Prefijo', required=True)
    min_value = fields.Integer('Rango Inicial', required=True)
    max_value = fields.Integer('Rango Final', required=True)
    number_next = fields.Integer('Siguiente número a usar', required=True)
    vitt_padding = fields.Integer('Número de relleno', required=True)
    company_id = fields.Many2one('res.company', "Empresa", default=lambda self: self.env.user.company_id)
    sequence_name = fields.Char("Nombre de secuencia")
    user_ids = fields.Many2many("res.users", string="Usuarios")
    new_sequence = fields.Boolean("Es una nueva secuencia")
    sequence_id = fields.Many2one("ir.sequence", "Secuencia Fiscal")
    doc_type = fields.Selection([
        ('out_invoice', 'Factura de clientes'),
        ('out_refund', 'Notas de Crédito'),
        ('in_refund', 'Notas de Débito'),
        ('in_invoice', 'Facturas de proveedores'),
    ], string='Tipo de documento', required=True)

    @api.onchange('min_value')
    def _onchange_min_value(self):
        if not self.number_next:
            self.number_next = self.min_value

    def fct_settings_fiscal(self):
        ctx = self._context
        obj_code_authorization = self.env["sar.authorization.code"].browse(ctx['active_id'])

        if self.number_next < self.min_value:
            raise UserError(_("'Next Number to Use' must be greater than 'Minimal Value'."))
        if self.number_next > self.max_value:
            raise UserError(_("'Next Number to Use' must be less than 'Max Value'."))

        if self.vitt_padding <= 0:
            raise UserError(_("Padding must be greater than zero."))
        if self.min_value >= self.max_value:
            raise UserError(_("Max Value must be greater than Minimal Value."))

        if self.new_sequence:
            if not self.sequence_name:
                raise UserError(_("Sequence name is empty."))
            else:
                self.fct_validated_exists()
                obj_fiscal_id = self.fct_fiscal_sequence_regime()
                if obj_fiscal_id:
                    obj_sequence_id = self.fct_sequence_create(obj_fiscal_id)
                    if obj_sequence_id:
                        obj_journal_id = self.fct_journal_sequence(obj_sequence_id)
                    else:
                        raise UserError(_("Sequence is not correct."))
        else:
            if self.sequence_id:
                for fiscal_line in self.sequence_id.fiscal_sequence_regime_ids:
                    if fiscal_line.authorization_code_id.id == obj_code_authorization.id:
                        raise UserError(_('This authorization code is already in use '))
                self.fct_validated_exists()
                obj_fiscal_id = self.fct_fiscal_sequence_regime()
                if obj_fiscal_id:
                    obj_sequence_id = self.fct_sequence_write(obj_fiscal_id, self.sequence_id.id)
                    if obj_sequence_id:
                        obj_journal_id = self.fct_journal_sequence(obj_sequence_id)
                    else:
                        raise UserError(_("Sequence is not correct."))
            else:
                raise UserError(_("You need select a sequence."))

    def fct_sequence_write(self, fiscal_sequence_id, sequence_id):
        obj_sequence = self.env["ir.sequence"].browse(sequence_id)
        ctx = self._context
        obj_code_authorization = self.env["sar.authorization_code"].browse(ctx['active_id'])
        obj_fiscal_sequence_regime = self.env["sar.fiscal_sequence_regime"].browse(fiscal_sequence_id)
        vitt_min_value = 0
        vitt_max_value = 0
        if self.vitt_prefix:
            start_number_filled = str(self.min_value)
            for filled in range(len(str(self.min_value)), self.vitt_padding):
                start_number_filled = '0' + start_number_filled
            vitt_min_value = self.vitt_prefix + str(start_number_filled)
            final_number = self.max_value
            final_number_filled = str(self.max_value)
            for filled in range(len(str(final_number)), self.vitt_padding):
                final_number_filled = '0' + final_number_filled
            vitt_max_value = self.vitt_prefix + str(final_number_filled)
        values = {'fiscal_sequence_regime_ids': [(4, obj_fiscal_sequence_regime.id, None)],
                  'min_value': self.min_value,
                  'max_value': self.max_value,
                  'expiration_date': obj_code_authorization.expiration_date,
                  'vitt_prefix': self.vitt_prefix,
                  'vitt_padding': self.vitt_padding,
                  'vitt_min_value': vitt_min_value,
                  'vitt_max_value': vitt_max_value,
                  'vitt_number_next_actual': self.number_next,
                  'code': self.doc_type, }
        sequence_write_id = obj_sequence.write(values)
        if sequence_write_id:
            for fiscal_regime in obj_sequence.fiscal_sequence_regime_ids:
                if fiscal_regime.id != obj_fiscal_sequence_regime.id:
                    fiscal_regime.actived = False
            if self.user_ids:
                users_vals = {}
                for users in self.user_ids:
                    users_vals = {
                        'user_ids': [(4, users.id, None)],
                    }
                if users_vals:
                    obj_sequence.write(users_vals)
                    obj_fiscal_sequence_regime.write(users_vals)

            sequence_write_id = obj_fiscal_sequence_regime.write({'sequence_id': sequence_id})
        obj_sequence.write({'number_next': self.number_next})
        return obj_sequence.id

    def fct_journal_sequence(self, obj_sequence_id):
        obj_sequence = self.env["ir.sequence"].browse(obj_sequence_id)
        for journal in self.journal_id:
            if not journal.allow_multi_sequence:
                journal.write({'allow_multi_sequence': True})
            journal.write({'sequence_ids': [(4, obj_sequence.id, None)]})
            obj_sequence.write({'journal_id': journal.id})
            return True

    def fct_validated_exists(self):
        sq_obj = self.env["ir.sequence"].search([('vitt_prefix', '=', self.vitt_prefix), ('vitt_padding', '=', self.vitt_padding), ('code', '=', self.doc_type),'|',('company_id', '=', self.company_id.id), ('journal_id', '=', self.journal_id.id)])
        for sq in sq_obj:
            if not self.number_next > sq.max_value or self.number_next < sq.min_value:
                raise UserError(_("The number exists already, please change the settings."))

    def fct_sequence_create(self, fiscal_sequence_id):
        obj_sequence = self.env["ir.sequence"]
        ctx = self._context
        obj_code_authorization = self.env["sar.authorization.code"].browse(ctx['active_id'])
        obj_fiscal_sequence_regime = self.env["sar.fiscal.sequence.regime"].browse(fiscal_sequence_id)
        vitt_min_value = 0
        vitt_max_value = 0
        if self.vitt_prefix:
            start_number_filled = str(self.min_value)
            for filled in range(len(str(self.min_value)), self.vitt_padding):
                start_number_filled = '0' + start_number_filled
            vitt_min_value = self.vitt_prefix + str(start_number_filled)
            final_number = self.max_value
            final_number_filled = str(self.max_value)
            for filled in range(len(str(final_number)), self.vitt_padding):
                final_number_filled = '0' + final_number_filled
            vitt_max_value = self.vitt_prefix + str(final_number_filled)
        sequence_validated = self.env["ir.sequence"].search([('vitt_prefix', '=', self.vitt_prefix), ('vitt_padding', '=', self.vitt_padding)])
        values = {'name': self.sequence_name,
                  'fiscal_sequence_regime_ids': [(4, obj_fiscal_sequence_regime.id, 0)],
                  'min_value': self.min_value,
                  'max_value': self.max_value,
                  'expiration_date': obj_code_authorization.expiration_date,
                  'cai': obj_code_authorization.name,
                  'prefix': self.vitt_prefix,
                  'padding': self.vitt_padding,
                  'vitt_min_value': vitt_min_value,
                  'vitt_max_value': vitt_max_value,
                  'is_fiscal_sequence': True,
                  'percentage_alert': 80.0,
                  'vitt_number_next_actual': self.number_next,
                  'code': self.doc_type, }
        sequence_id = obj_sequence.create(values)
        if sequence_id:
            users_vals = {}
            for users in self.user_ids:
                users_vals = {
                    'user_ids': [(4, users.id, 0)],
                }
            if users_vals:
                obj_sequence.write(users_vals)
                obj_fiscal_sequence_regime.write(users_vals)

            obj_fiscal_sequence_regime.write({'sequence_id': sequence_id.id})

        sequence_id.write({'number_next': self.number_next})
        return sequence_id.id

    def fct_fiscal_sequence_regime(self):
        obj_fiscal_sequence_regime = self.env["sar.fiscal.sequence.regime"]
        ctx = self._context
        obj_code_authorization = self.env["sar.authorization.code"].browse(ctx['active_id'])
        values = {'authorization_code_id': obj_code_authorization.id,
                  '_from': self.min_value,
                  '_to': self.max_value,
                  'journal_id': self.journal_id.id,
                  'actived': True}
        obj_fiscal_id = obj_fiscal_sequence_regime.create(values)
        return obj_fiscal_id.id
