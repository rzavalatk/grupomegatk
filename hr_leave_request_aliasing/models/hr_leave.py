# -*- coding: utf-8 -*-
import re
from datetime import datetime
from odoo import api, models
from odoo.tools import email_split


class HrLeave(models.Model):
    """Extensión del modelo de Ausencias para crear solicitudes desde correos.
    
    Permite la creación automática de solicitudes de ausencias a partir de
    correos electrónicos entrantes. El sistema extrae información del correo
    como fechas, empleado y razón para crear la solicitud automáticamente.
    
    Formato esperado del correo:
    - Asunto: Debe comenzar con el prefijo configurado (ej: "SOLICITUD DE AUSENCIA")
    - Remitente: Debe ser el correo del empleado registrado
    - Cuerpo: Debe incluir fechas en formato DD/MM/YYYY
    """
    _inherit = 'hr.leave'

    # ===== MÉTODOS DE PROCESAMIENTO DE MENSAJES =====
    
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """Crea una solicitud de ausencia desde un correo electrónico entrante.
        
        Este método procesa correos entrantes y extrae la información necesaria
        para crear automáticamente una solicitud de ausencia. Realiza las
        siguientes operaciones:
        
        1. Valida que el asunto contenga el prefijo configurado
        2. Valida que el dominio del remitente coincida con la configuración
        3. Identifica al empleado por su correo electrónico
        4. Extrae las fechas del cuerpo del mensaje (formato DD/MM/YYYY)
        5. Calcula la duración de la ausencia
        6. Crea la solicitud con los datos extraídos
        
        Args:
            msg_dict (dict): Diccionario con los datos del correo electrónico
                - subject: Asunto del correo
                - email_from: Dirección del remitente
                - body: Cuerpo del mensaje (HTML)
            custom_values (dict, optional): Valores personalizados adicionales
            
        Returns:
            recordset: Registro de ausencia creado
            
        Ejemplo de correo válido:
            Asunto: "SOLICITUD DE AUSENCIA - Vacaciones"
            De: empleado@empresa.com
            Cuerpo: "Solicito ausencia del 15/01/2026 al 20/01/2026"
        """
        if custom_values is None:
            custom_values = {}
        
        # Extrae información básica del correo
        msg_subject = msg_dict.get('subject', '')
        mail_from = msg_dict.get('email_from', '')
        
        # Obtiene el prefijo y dominio configurados en ajustes
        prefix = self.env['ir.config_parameter'].sudo().get_param(
            'hr_holidays.alias_prefix')
        domain = self.env['ir.config_parameter'].sudo().get_param(
            'hr_holidays.alias_domain')
        
        # Valida que el asunto contenga el prefijo configurado
        subject = re.search(prefix, msg_subject)
        # Valida que el dominio del remitente sea correcto
        from_mail = re.search(domain, mail_from)
        
        if subject and from_mail:
            # Extrae la dirección de correo del remitente
            email_address = email_split(msg_dict.get('email_from', False))[0]
            
            # Busca el empleado por correo electrónico
            employee = self.env['hr.employee'].sudo().search(
                ['|', ('work_email', 'ilike', email_address),
                 ('user_id.email', 'ilike', email_address)], limit=1)
            
            # Procesa el cuerpo del mensaje
            msg_body = msg_dict.get('body', '')
            # Elimina todas las etiquetas HTML del mensaje
            cleaner = re.compile('<.*?>')
            clean_msg_body = re.sub(cleaner, '', msg_body)
            
            # Busca fechas en formato DD/MM/YYYY en el mensaje
            date_list = re.findall(r'\d{2}/\d{2}/\d{4}', clean_msg_body)
            
            if len(date_list) > 0:
                # Primera fecha encontrada = fecha de inicio
                start_date = datetime.strptime(date_list[0], '%d/%m/%Y')
                
                if len(date_list) == 1:
                    # Si solo hay una fecha, la ausencia es de un día
                    date_to = start_date
                else:
                    # Segunda fecha = fecha de fin
                    date_to = datetime.strptime(date_list[1], '%d/%m/%Y')
                
                # Calcula el número de días de ausencia
                no_of_days_temp = (
                        datetime.strptime(str(date_to), "%Y-%m-%d %H:%M:%S") -
                        datetime.strptime(str(start_date), '%Y-%m-%d %H:%M:%S')
                ).days
                
                # Configura los valores para crear la solicitud de ausencia
                custom_values.update({
                    'name': msg_subject.strip(),  # Título = asunto del correo
                    'employee_id': employee.id,   # Empleado identificado
                    'holiday_status_id': self.env['hr.leave.type'].search(
                        [('requires_allocation', '=', 'no')])[0].id,  # Tipo de ausencia
                    'request_date_from': start_date,  # Fecha de inicio
                    'request_date_to': date_to,       # Fecha de fin
                    'duration_display': no_of_days_temp + 1  # Duración en días
                })
        
        # Llama al método original para crear el registro
        return super().message_new(msg_dict, custom_values)
