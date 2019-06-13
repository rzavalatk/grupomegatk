# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import Warning


class SequenceJournal(models.TransientModel):
    _name = "vitt.banks.journal.settings"
    _description = "Journal Settings"



    journal_id = fields.Many2one("account.journal", "Diario")
    fecha = fields.Date("Fecha")
    name = fields.Char("Referencia")

    
    