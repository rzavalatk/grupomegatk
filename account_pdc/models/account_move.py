# -*- coding: utf-8 -*-
from odoo import models, fields


class AccountMove(models.Model):
    _inherit = "account.move"

    # Override: Quitar el requisito de team_id que viene del core de Odoo v18
    # Nota: fields_megatk.Account_Move ya maneja la lógica completa de asegurar team_id
    team_id = fields.Many2one(
        'crm.team',
        check_company=True,
        required=False,
    )
