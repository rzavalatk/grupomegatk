# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MedicalQuestions(models.Model):
    """Para agregar preguntas del cuestionario médico"""
    _name = 'medical.questions'
    _description = 'Preguntas Médicas'
    _rec_name = 'question'

    question = fields.Char(string='Pregunta', help='Pregunta médica para el paciente')

    @api.model
    def create(self, vals):
        """Sobrescribe el método create para agregar una nueva pregunta médica
        y crear automáticamente una entrada correspondiente en el modelo
        `medical.questionnaire`."""
        res = super(MedicalQuestions, self).create(vals)
        self.env['medical.questionnaire'].create({
            'question_id': res.id
        })
        return res

    def unlink(self): 
        """Sobrescribe el método unlink para eliminar el registro actual de pregunta médica.
        Antes de la eliminación, busca y elimina cualquier registro asociado en el modelo
        `medical.questionnaire` que haga referencia a esta pregunta médica."""
        for rec in self:
            for line in self.env['medical.questionnaire'].search(
                    [('question_id', '=', rec.id)]):
                line.unlink()
            return super(MedicalQuestions, self).unlink()
