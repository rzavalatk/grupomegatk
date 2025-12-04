# -*- coding: utf-8 -*-
from odoo import fields, models


class MedicalQuestionnaire(models.Model):
    """Preguntas médicas que se harán a los pacientes durante su cita"""
    _name = 'medical.questionnaire'
    _description = 'Cuestionario Médico' 

    question_id = fields.Many2one('medical.questions',
                                  string='Preguntas',
                                  help="Todas las preguntas agregadas")
    yes_no = fields.Selection([('yes', 'Sí'), ('no', 'No')],
                              string='Sí o No', help="")
    reason = fields.Text(string='Razón', help="Razón para la respuesta a la pregunta")
    patient_id = fields.Many2one('res.partner',
                                 string='Paciente',
                                 help="Nombre del paciente")
