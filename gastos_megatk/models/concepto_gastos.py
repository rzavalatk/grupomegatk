# -*- encoding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class Concetogastos(models.Model):
    _name = "gastos.megatk.conceptos"
    _inherit = ['mail.thread']
    _description = "description"


    name = fields.Char("Nombre de gastos", required=True)
