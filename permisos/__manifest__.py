# -*- coding: utf-8 -*-
{
    'name': "permisos",

    'summary': """
        Solicitud y aprobacion de permisos, Calculo de vaciones""",

    'description': """
        Solicitud y aprobacion de permisos, Calculo de vaciones""",

    'author': "Romel Zavala",
    'website': "https://www.megatk.net",
    "license": "LGPL-3",

    'category': 'Human Resources',
    'version': '0.1',

    'depends': ['base','hr', 'hr_holidays'],

    'data': [
        "security/groups.xml",
        'security/ir.model.access.csv',
        "wizard/wizard_solicitar_permiso.xml",
        #'data/hr_leave_data.xml',
        'views/default_views.xml',
        'views/permisos_views.xml',
        'views/hr_views.xml',
        'views/email_template.xml',
        'views/hr_leave_view.xml',
        'views/hr_leave_type_view.xml',
        'views/templates_timeoff.xml',
        
    ],
    #'assets': {
     #   'web.assets_backend': [
     #       '/permisos/static/src/xml/templates_timeoff.xml',
     #   ],
    #},

}