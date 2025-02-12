# # -*- coding: utf-8 -*-
# from odoo import fields, models, api
# from odoo.exceptions import UserError
# from datetime import date

# class Visitas_Record(models.Model):
#     _name = 'registro.visitas'
#     _description = 'Modelo de visitas diarias a las sucursales'
    
#     fecha_reporte = fields.Date(string='Fecha', compute='_compute_fecha', store=True)
#     company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company.id, required=True)
    
#     visita_diaria = fields.One2many('control.visitas', 'registro_visita', string='Registro Visitas')

#     def _compute_fecha(self):
#         for record in self:
#             record.fecha_reporte = date.now()

#     def agrupar_registros(self):
#         visitas = self.env['control.visitas'].sudo().search([('fecha', '=', self.fecha_reporte)])
        
#         if not visitas:
#             raise UserError("No hay registros de visitas")
#         else:
#             self.visita_diaria = visitas
        
        