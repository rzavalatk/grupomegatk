from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Users(models.Model):
    _inherit = "res.users"

    access_right_ids = fields.One2many('ir.model.access', 'user_id')
    