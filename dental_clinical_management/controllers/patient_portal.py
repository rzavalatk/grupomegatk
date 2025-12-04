# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers import portal


class PatientPortal(portal.CustomerPortal):
    """Proporciona acceso al portal para que los pacientes vean sus detalles
    de tratamiento, recetas y facturas."""
    def _prepare_home_portal_values(self, counters):
        """Extiende el método base para incluir el conteo de recetas dentales
        en el diccionario devuelto si se solicita.
        Args:
            counters (list): Una lista de cadenas que indica qué conteos
            incluir en la respuesta."""
        values = super()._prepare_home_portal_values(counters)
        if 'prescriptions_count' in counters:
            prescriptions_count = request.env['dental.prescription'].sudo().search_count([])
            values['prescriptions_count'] = prescriptions_count
        return values

    @http.route(['/mis/recetas'], type='http', auth="user", website=True)
    def portal_my_prescriptions(self, **kwargs):
        """Renderiza la página de recetas para el usuario autenticado según su rol.
        Los gerentes ven todas las recetas, los doctores ven las suyas, y los pacientes ven
        sus propias recetas."""
        if request.env.ref('dental_clinical_management.group_dental_manager') in request.env.user.groups_id:
            domain = []
        elif request.env.ref('dental_clinical_management.group_dental_doctor') in request.env.user.groups_id:
            domain = [('prescribed_doctor_id', '=', request.env.user.partner_id.employee_ids.id)]
        else:
            domain = [('patient_id', '=', request.env.user.partner_id.id)]
        prescriptions = request.env['dental.prescription'].sudo().search(domain)
        return request.render("dental_clinical_management.portal_my_prescriptions",
                              {'prescriptions': prescriptions, 'page_name': 'prescriptions'})

    @http.route(['/ver/receta/<int:id>'],
                type='http', auth="public", website=True)
    def view_prescriptions(self, id):
        """Ver recetas basándose en el ID proporcionado.
        :param id: El ID de la receta a visualizar.
        :return: Plantilla renderizada con los detalles de la receta."""
        prescription = request.env['dental.prescription'].browse(id)
        return request.render('dental_clinical_management.prescription_portal_template',
                              {'prescription_details': prescription, 'page_name': 'prescription'})
