# -*- coding: utf-8 -*-
{
    'name': "Planilla y metas",
    'summary': """
        Modulo para manejar planilla y metas de los empleados
        """,
    'description': """
        Modulo para manejar planilla y metas de los empleados
    """,
    'author': "Alejandro Zelaya",
    'website': "azelaya@megatk.com",
    'category': 'employees',
    'version': '0.1',
    'depends': ['base','hr'],
    'data': [
        'security/security.xml',
        'wizard/wizard.xml',
        'data/data_hr_metas_default.xml',
        'views/menus.xml', 
        'views/planilla/deductions.xml', 
        'views/planilla/file_employee.xml', 
        'views/planilla/spreadsheet.xml', 
        'views/metas/hr_employee.xml', 
        'views/metas/hr_metas.xml', 
        'views/metas/hr_metas_asignadas.xml', 
        'views/metas/hr_metas_default.xml', 
        'views/metas/hr_metas_default_asignada.xml', 
        'views/metas/hr_resultados.xml', 
        'static/template/email_avances.xml',
        'static/template/pdf_template.xml',
        'static/template/email_resultados.xml',
    ],
}