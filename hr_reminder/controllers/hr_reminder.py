# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import http, fields
from odoo.http import request


class Reminders(http.Controller):
    """Controlador para gestionar recordatorios de RRHH.
    
    Proporciona endpoints JSON para:
    - Listar todos los recordatorios activos
    - Obtener detalles de un recordatorio específico para su visualización
    """
    
    @http.route('/hr_reminder/all_reminder', type='json', auth="public")
    def all_reminder(self):
        """Retorna todos los recordatorios activos según su configuración.
        
        Evalúa cada recordatorio y determina si debe mostrarse basándose en:
        - 'today': Se muestra siempre
        - 'set_period': Se muestra si la fecha actual está dentro del rango
        - 'set_date': Se muestra si estamos dentro del período de anticipación
        
        Returns:
            list: Lista de diccionarios con 'id' y 'name' de recordatorios activos
        """
        reminders = []
        for reminder in request.env['hr.reminder'].search([]):
            # Recordatorios de tipo "Hoy" siempre se muestran
            if reminder.search_by == 'today':
                reminders.append({
                    'id': reminder.id,
                    'name': reminder.name
                })
            # Recordatorios por período: verificar si estamos dentro del rango
            elif reminder.search_by == 'set_period':
                if (fields.date.today() >=
                        reminder.date_from and fields.date.today()
                        <= reminder.date_to and (
                        not reminder.expiry_date or fields.date.today()
                        <= reminder.expiry_date)):
                    reminders.append({
                        'id': reminder.id,
                        'name': reminder.name
                    })
            # Recordatorios por fecha: verificar días antes y fecha de expiración
            else:
                if fields.date.today() >= reminder.date_set - timedelta(
                        days=reminder.days_before) and (
                        not reminder.expiry_date or fields.date.today()
                        <= reminder.expiry_date):
                    reminders.append({
                        'id': reminder.id,
                        'name': reminder.name
                    })
        return reminders

    @http.route('/hr_reminder/reminder_active', type='json', auth="public")
    def reminder_active(self, **kwargs):
        """Obtiene la configuración completa de un recordatorio específico.
        
        Retorna todos los datos necesarios para mostrar los registros
        correspondientes al recordatorio seleccionado en el systray.
        
        Args:
            **kwargs: Debe incluir 'reminder_name' con el nombre del recordatorio
        
        Returns:
            list: Lista con los datos del recordatorio en el siguiente orden:
                [0] model: Nombre del modelo
                [1] field_name: Nombre del campo de fecha
                [2] search_by: Tipo de búsqueda
                [3] date_set: Fecha establecida
                [4] date_from: Fecha desde
                [5] date_to: Fecha hasta
                [6] id: ID del recordatorio
                [7] today: Fecha actual
                [8] field_type: Tipo de campo (date/datetime)
                [9] days_before: Días de anticipación
                [10] calculated_date: Fecha calculada (date_set - days_before)
        """
        value = []
        for reminder in request.env['hr.reminder'].sudo().search([
                ('name', '=', kwargs.get('reminder_name'))]):
            # Agrega toda la información del recordatorio al array
            value.append(reminder.model_id.model)  # [0] Modelo
            value.append(reminder.field_id.name)   # [1] Campo
            value.append(reminder.search_by)       # [2] Tipo de búsqueda
            value.append(reminder.date_set)        # [3] Fecha establecida
            value.append(reminder.date_from)       # [4] Fecha desde
            value.append(reminder.date_to)         # [5] Fecha hasta
            value.append(reminder.id)              # [6] ID
            value.append(fields.Date.today())      # [7] Fecha actual
            value.append(reminder.field_id.ttype)  # [8] Tipo de campo
            value.append(reminder.days_before)     # [9] Días antes
            
            # Si hay fecha establecida, calcula la fecha considerando días antes
            if reminder.date_set:
                value.append(reminder.date_set - timedelta(
                        days=reminder.days_before))  # [10] Fecha calculada
        return value
