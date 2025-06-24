# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class pos_slide_to_delete(models.Model):
#     _name = 'pos_slide_to_delete.pos_slide_to_delete'
#     _description = 'pos_slide_to_delete.pos_slide_to_delete'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
