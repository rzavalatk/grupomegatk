# -*- coding: utf-8 -*-
{
    'name': 'Open HRMS - Vencimiento de Documentos de Empleados',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Gestiona Documentos de Empleados con Notificaciones de Vencimiento.""",
    'description': """Módulo OH: Gestiona Documentos Relacionados con Empleados con 
     Notificaciones de Vencimiento. A medida que se acercan tales fechas, el sistema 
     está programado para enviar alertas automatizadas a los empleados relevantes. 
     Estas notificaciones oportunas son esenciales para asegurar que se puedan tomar 
     las acciones necesarias para actualizar o renovar documentos antes de que caduquen, 
     evitando así potenciales complicaciones legales, regulatorias u operacionales que 
     puedan surgir de documentación vencida.""",
    'author': 'David Zuniga - MegaTK',
    'company': 'MegaTK',
    'maintainer': 'MegaTK',
    'website': "https://www.megatk.com",
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/document_type_views.xml',
        'views/hr_document_views.xml',
        'views/hr_employee_document_views.xml',
    ],
    'demo': [
        'data/document_type_demo.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
