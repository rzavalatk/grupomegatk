# -*- coding: utf-8 -*-
from odoo import fields, models


class MedicineFrequency(models.Model):
    """Para especificar la frecuencia del medicamento, cómo consumirlo."""
    _name = 'medicine.frequency'
    _description = "Frecuencia del Medicamento"
    _rec_name = "medicament_frequency"

    code = fields.Char(string="Código", help="Código de la frecuencia del medicamento")
    medicament_frequency = fields.Char(string="Frecuencia del Medicamento",
                                       help="Agregar la frecuencia del medicamento cómo consumirlo")