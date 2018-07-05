# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date

class Helpdesk(models.Model):
    _inherit = "helpdesk.ticket"

    x_fechai = fields.Date(string= 'Inicio',required=True,default =date.today())    
    x_fechaf = fields.Date(string='Final',required=True)