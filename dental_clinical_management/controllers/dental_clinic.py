# -*- coding: utf-8 -*-
from odoo.exceptions import UserError
from odoo import _, http
from odoo.http import Controller, request, route


class DentalClinic(Controller):
    """Controlador para un sitio web de clínica dental que permite a los usuarios ver detalles de la clínica
    y programar citas en línea."""

    @route('/dental_doctor', auth='public', website=True)
    def dental_clinic(self):
        """Renderiza la página de la clínica dental con información del paciente, especialista y doctor.
        Este método recupera el ID del socio del usuario actual como el ID del paciente,
        obtiene todos los registros del modelo `dental.specialist` y todos los registros
        del modelo `hr.employee` para mostrar en la página web de la clínica dental."""
        patient_id = request.env.user.partner_id
        specialised_id = request.env['dental.specialist'].sudo().search([])
        doctor_id = request.env['hr.employee'].sudo().search([])
        return request.render(
            'dental_clinical_management.website_dental_template',
            {'patient_id': patient_id,
             'specialised_id': specialised_id,
             'doctor_id': doctor_id})

    @route('/create/citaMedica', auth='public', website=True)
    def create_appointment(self, **kw):
        """Para crear una nueva cita desde el sitio web de la clínica dental.
        Este método verifica si ya existe una cita para el paciente, doctor,
        fecha y turno dados. Si existe, renderiza una plantilla indicando que la
        cita ya está programada. Si no existe, crea una nueva cita con los
        detalles proporcionados y redirige a una página de éxito con el token
        de la cita, el ID del doctor y el número de secuencia."""
        appointment_exists = request.env['dental.appointment'].sudo().search(
            [('patient_id', '=', int(kw.get('patient'))),
             ('doctor_id', '=', int(kw.get('doctor'))),
             ('date', '=', kw.get('date')),
             ('shift_id', '=', int(kw.get('time_shift')))])

        if appointment_exists:
            return request.render(
                'dental_clinical_management.website_dental_scheduled_template',
            )
        if len(kw.get('time_shift')) == 0:
            raise UserError(_('Doctor No tiene cita disponible en este turno'))
        else:
            patient_appointment = request.env[
                'dental.appointment'].sudo().create({
                    'patient_id': kw.get('patient'),
                    'patient_phone': kw.get('phone'),
                    'patient_age': kw.get('age'),
                    'specialist_id': kw.get('specialization', False),
                    'doctor_id': kw.get('doctor'),
                    'shift_id': kw.get('time_shift'),
                    'date': kw.get('date'),
                })
            return request.redirect(
                f'/Cita_exitosa?token={patient_appointment.token_no}'
                f'&doctor_id={patient_appointment.doctor_id}'
                f'&sequence_no={patient_appointment.sequence_no}')

    @route('/Cita_exitosa', auth='public', website=True)
    def success_appointment(self, **kwargs):
        """Retorna cuando la creación de la cita es exitosa.
        Renderiza una plantilla de éxito con el token de la cita."""
        return request.render(
            'dental_clinical_management.website_rental_success_template',
            {'token': kwargs})

    @http.route('/clinica_dental/datos_cita/<token>',
                type='http', auth="public", website=True)
    def appointment_card(self, token):
        """Para descargar la tarjeta de cita para los pacientes para la cita del doctor.
        Este método busca una cita en el modelo `dental.appointment` utilizando
        el token proporcionado. Si se encuentra la cita, genera un PDF de la
        tarjeta de cita con los detalles de la cita y lo devuelve como una
        respuesta HTTP. Si no se encuentra la cita, devuelve una respuesta de
        "no encontrado"."""
        appointment = request.env['dental.appointment'].sudo().search(
            [('sequence_no', '=', token)])
        if not appointment.exists():
            return request.not_found()
        data = {
            'token': appointment.token_no,
            'doctor': appointment.doctor_id.name,
            'specialised': appointment.specialist_id.name,
            'appointment_time': appointment.shift_id.name,
            'date': appointment.date,
        }
        report_action = request.env.ref(
            'dental_clinical_management.action_appointment_card')
        pdf_content, _ = report_action.sudo()._render_qweb_pdf(
            'dental_clinical_management.dental_clinical_management_appointment_card',
            data=data)
        pdf_http_headers = [('Content-Type', 'application/pdf'),
                            ('Content-Length', len(pdf_content))]
        return request.make_response(pdf_content, headers=pdf_http_headers)

    @route('/detalles_paciente', type="json", auth='public', website=True)
    def get_patient_details(self, patient_id):
        """ Recupera y devuelve los detalles de un paciente específico por su ID.
        Este método accede al modelo `res.partner`, recupera un registro de paciente
        por el ID dado y devuelve campos seleccionados del paciente
        como el número de teléfono y la edad.
        Args:
            patient_id (int): El identificador único del paciente."""
        patient = request.env['res.partner'].sudo().browse(int(patient_id))
        return patient.read(fields=['phone', 'patient_age'])

    @route('/doctores_especializados', type="json", auth='public', website=True)
    def get_specialised_doctors(self, specialised_id):
        """Para obtener la lista de doctores según su especialización"""
        domain = []
        if specialised_id:
            domain = [('specialised_in_id', '=', int(specialised_id))]
        doctors = request.env['hr.employee'].sudo().search_read(domain,
                                                                ["name"])
        return doctors

    @route('/horarios_doctores', type="json", auth='public', website=True)
    def get_doctors_shifts(self, doctor_id):
        """Para obtener los horarios de un doctor en particular"""
        doctors_shift = request.env['hr.employee'].sudo().browse(
            int(doctor_id)).time_shift_ids
        time_shifts = [{"id": rec.id, "name": rec.name} for rec in
                       doctors_shift]
        return time_shifts

    @route('/todos_los_doctores', auth='public', website=True)
    def get_all_doctors(self):
        """Para listar todos los doctores disponibles en la clínica dental"""
        doctor_id = request.env['hr.employee'].sudo().search([])
        return request.render('dental_clinical_management.website_all_doctors',
                              {'doctor_ids': doctor_id})
