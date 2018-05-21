# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class SequenceJournal(models.TransientModel):
    _name = "vitt.banks.journal.settings"
    _description = "Journal Settings"

    @api.multi
    def get_journal(self):
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        journal = self.env[active_model].browse(active_ids)
        return journal

    journal_id = fields.Many2one("account.journal", "Journal", default=get_journal)
    vitt_prefix = fields.Char('Prefix', required=True)
    min_value = fields.Integer('Start number checkbook')
    max_value = fields.Integer('End number checkbook')
    vitt_padding = fields.Integer('Digits Number', required=True, default=4)
    company_id = fields.Many2one('res.company', "Company")
    sequence_name = fields.Char("Transaction name")
    new_sequence = fields.Boolean("Is a new transaction")
    number_next = fields.Integer('Next Number to Use', required=True)
    sequence_id = fields.Many2one("ir.sequence", "Transaction", domain="[('journal_id','=', journal_id),('code','=',doc_type)]")
    doc_type = fields.Selection([
        ('check', 'Checks'),
        ('tranasfer', 'Transference'),
        ('debit', 'Debit'),
        ('credit', 'Credit'),
        ('deposit', 'Deposit'),
        ('banks_transference', 'Banks transferences'),
    ], string='Transaction Type', default='check', required=True)

    @api.onchange("doc_type")
    def onchange_doc_type(self):
        if self.journal_id:
            self.min_value = 0
            self.number_next = 1
            if self.journal_id.sequence_ids:
                max_value_num = 0
                next_number = 0
                for jr_seq in self.journal_id.sequence_ids:
                    if self.doc_type == jr_seq.code:
                        max_value_num = jr_seq.max_value
                        next_number = jr_seq.number_next_actual
                if max_value_num > 0:
                    self.number_next = max_value_num + 1
                    self.min_value = max_value_num + 1
                else:
                    if next_number > 0:
                        self.number_next = next_number
        else:
            raise Warning(_("Select a journal."))

    @api.one
    def fct_sequence_settings(self):
        ctx = self._context
        journal_id = self.env["account.journal"].browse(ctx['active_id'])
        obj_sequence_id = False
        if self.vitt_padding <= 0:
            raise Warning(_("Padding must be greater than zero."))
        if self.doc_type == 'check':
            if not (self.min_value and self.max_value):
                raise Warning(_("Set a minimal and max value."))
            if self.min_value >= self.max_value:
                raise Warning(_("Max Value must be greater than Minimal Value."))
            if self.number_next < self.min_value:
                raise Warning(_("'Next Number to Use' must be greater than 'Minimal Value'."))
            if self.number_next > self.max_value:
                raise Warning(_("'Next Number to Use' must be less than 'Max Value'."))
        if self.new_sequence:
            if not self.sequence_name:
                raise Warning(_("Transaction name is empty."))
            else:
                if self.doc_type == 'check':
                    validated_max = True
                    for jr_seq in journal_id.sequence_ids:
                        if jr_seq.code == 'check':
                            if self.min_value >= jr_seq.max_value:
                                validated_max = True
                            else:
                                validated_max = False
                    if not validated_max:
                        raise Warning(_("the range the numbers for the check book already exists, the number you can use is ."))
                if not self.doc_type == 'check':
                    if journal_id.sequence_ids:
                        for jr_seq in journal_id.sequence_ids:
                            if jr_seq.code == self.doc_type:
                                raise Warning(_("This transacion type already exists."))
                obj_sequence_id = self.fct_sequence_create(journal_id.id)
                if not obj_sequence_id:
                    raise Warning(_("Journal settings failed."))
        else:
            if self.sequence_id:
                if self.doc_type == 'check':
                    validated_max = False
                    for jr_seq in journal_id.sequence_ids:
                        if jr_seq.code == 'check':
                            if self.min_value >= jr_seq.max_value:
                                validated_max = True
                            else:
                                validated_max = False
                    if validated_max:
                        pass
                    else:
                        raise Warning(_("the range the numbers for the check book already exists, the number you can use is ."))
                obj_sequence_id = self.fct_sequence_write(self.sequence_id.id)
            else:
                raise Warning(_("You need select a sequence."))

    def fct_sequence_write(self, sequence_id):
        obj_sequence = self.env["ir.sequence"].browse(sequence_id)
        values = {
        'min_value': self.min_value,
        'max_value': self.max_value,
        'prefix': self.vitt_prefix,
        'padding': self.vitt_padding,
        'code': self.doc_type
        }
        obj_sequence.write(values)
        obj_sequence.write({'number_next': self.number_next})
        return obj_sequence.id

    def fct_sequence_create(self, journal_id):
        obj_sequence = self.env["ir.sequence"]
        journal = self.env["account.journal"].search([('id', '=', journal_id)])
        values = {
          'name': self.sequence_name,
          'prefix': self.vitt_prefix,
          'padding': self.vitt_padding,
          'min_value': self.min_value,
          'max_value': self.max_value,
          'implementation': 'no_gap',
          'code': self.doc_type,
          'journal_id': journal.id,
          'company_id': journal.company_id.id, }
        sequence_id = obj_sequence.create(values)
        obj_sequence.write({'number_next': self.number_next})
        if sequence_id:
            journal.write({'sequence_ids': [(4, sequence_id.id, None)]})
        return sequence_id.id
