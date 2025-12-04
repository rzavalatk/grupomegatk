# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DentalTimeShift(models.Model):
    """Turno de tiempo de los médicos, diferentes franjas horarias"""
    _name = 'dental.time.shift'
    _description = "Turno de Tiempo Dental"
    _rec_name = 'name'

    name = fields.Char(string='Nombre', readonly=True,
                       help="nombre de los turnos de tiempo")
    shift_type = fields.Selection(
        selection=[('morning', 'Mañana'), ('day', 'Día'),
                   ('evening', 'Tarde'), ('night', 'Noche')],
        string="Tipo de Turno", help="Campo de selección para el tipo de turno")
    start_time = fields.Float(string="Hora de Inicio", help="hora de inicio del turno", required=True)
    end_time = fields.Float(string="Hora de Fin", help="hora de fin del turno", required=True)

    @api.model_create_multi
    def create(self, vals_list):
        """Sobrescribe el método create para establecer el campo `name` de los
        registros `dental.time.shift` recién creados a una cadena que representa
        el rango de tiempo del turno.""" 
        res = super(DentalTimeShift, self).create(vals_list)
        res.name = f'{res.start_time} a {res.end_time}'
        return res

    @api.onchange('start_time', 'end_time')
    def _onchange_time(self):
        name = f'{self.start_time} a {self.end_time}'
        self.update({'name': name})

