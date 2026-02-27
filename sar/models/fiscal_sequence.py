# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Authorization(models.Model):
    _name = "sar.authorization.code"
    _description = "description"

    name = fields.Char('Código de autorización', help='Código de autorización', required=True)
    expiration_date = fields.Date('Fecha de expiración', required=True)
    start_date = fields.Date('Fecha de inicio', help='start date', required=True)
    company_id = fields.Many2one('res.company', "Empresa", default=lambda self: self.env.user.company_id, required=True)
    code_type = fields.Many2one('sar.authorization.code.type', string='Tipo', help='tax regime type code', required=True)
    active = fields.Boolean("Activo", default=True)
    fiscal_sequence_regime_ids = fields.One2many('sar.fiscal.sequence.regime', 'authorization_code_id')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Authorization, self).create(vals_list)
        if vals_list.get("start_date") > vals_list.get("expiration_date"):
            raise UserError(_('Start date is greater than than expiration date'))
        return res

    def _update_ir_sequence(self):
        for fiscal_sequence in self.fiscal_sequence_regime_ids:
            if fiscal_sequence.sequence_id:
                sequence_vals = {'expiration_date': self.expiration_date}
                fiscal_sequence.sequence_id.write(sequence_vals)
        return True

    def write(self, vals_list):
        res = super(Authorization, self).write(vals_list)
        res = self._update_ir_sequence()
        return res

class Fiscal_sequence(models.Model):
    _name = "sar.fiscal.sequence.regime"
    _description = "description"

    authorization_code_id = fields.Many2one('sar.authorization.code', required=True)
    sequence_id = fields.Many2one('ir.sequence', "Fiscal Number")
    actived = fields.Boolean('Active')
    _from = fields.Integer('From')
    _to = fields.Integer('to')
    user_ids = fields.Many2many("res.users", string="Users", related="sequence_id.user_ids")
    journal_id = fields.Many2one("account.journal", "Journal")

    def build_numbers(self, number):
        res = ''
        prefix = self.sequence_id.prefix
        padding = self.sequence_id.padding
        if padding and prefix and number:
            res = prefix + str(number).zfill(padding)
        return res

    def _update_ir_sequence(self):
        if self.sequence_id:
            sequence_vals = {'vitt_min_value': self.build_numbers(self._from),
                             'vitt_max_value': self.build_numbers(self._to),
                             }
            self.sequence_id.write(sequence_vals)

    @api.onchange("actived")
    def onchange_actived(self):
        if not self.actived:
            for sequence in self.sequence_id:
                self.sequence_id.write({'active': False})
        if self.actived and not self.sequence_id.active:
            self.sequence_id.write({'active': True})
    
    def write(self, vals_list):
        super(Fiscal_sequence, self).write(vals_list)
        self._update_ir_sequence()
    
    def _review_index(self,index,array):
        try:
            array[index]
            return True
        except :
            return False

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Fiscal_sequence, self).create(vals_list)
        if not vals_list.get('journal_id'):
            raise UserError(_('Set a journal and a sequence'))
        return res

    # TODO : Verificar que no exista en facturas esta secuencia
    #@api.multi
    #def unlink(self):
        #invoice = self.env["account.invoice"].search([('sequence_ids', '=', self.sequence_id.id)])
        #if invoice:
            #raise UserError(_('You cannot delete a fiscal regime, you must disable it'))
        #return super(Fiscal_sequence, self).unlink()


class Code_authorization_type(models.Model):
    _name = "sar.authorization.code.type"
    _description = "description"

    name = fields.Char('Nombre', help='tax regime type', required=True)
    description = fields.Char('Descripción', help='tax regime type description', required=True)

    _sql_constraints = [('value_code_authorization_type_uniq', 'unique (name)', 'Only one authorization type is permitted!')]
