# -*- coding: utf-8 -*-
{
    'name': "Open HRMS - Dashboard de RRHH",
    'version': '18.0.1.0.0',
    'summary': """Open HRMS - Panel de Control de Recursos Humanos""",
    'description': """Panel de control interactivo para Open HRMS con gráficos 
    y estadísticas de empleados, asistencias, ausencias y nóminas""",
    'category': 'Generic Modules/Human Resources',
    'live_test_url': 'https://youtu.be/XwGGvZbv6sc',
    'author': 'Cybrosys Techno solutions,Open HRMS',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.openhrms.com",
    'depends': ['hr', 'hr_holidays', 'hr_skills', 'hr_timesheet',
                'hr_attendance', 'hr_timesheet_attendance',
                'hr_recruitment', 'hr_resignation', 'event',
                'hr_reward_warning','hr_expense'],
    'external_dependencies': {
        'python': ['pandas'],
    },
    'data': [
        'security/ir.model.access.csv',
        'report/broadfactor.xml',
        'views/hr_leave_views.xml',
        'views/hrms_dashboard_menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hrms_dashboard/static/src/css/dashboard.css',
            'hrms_dashboard/static/src/js/dashboard.js',
            'hrms_dashboard/static/src/xml/dashboard.xml',
            'https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.9.4/Chart.js',
        ],
    },
    'images': ["static/description/banner.jpg"],
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
}
