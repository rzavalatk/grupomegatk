{
    'name': 'Control de Visitas',
    'version': '1.2',
    'description': 'Modulo para controlar visitas a las diferentes sucursales',
    'summary': 'Modulo para controlar visitas',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/control_visita_mail.xml',
        'views/registros_visitas_view.xml',
        'views/reportes_visitas_view.xml',
        'views/visitas_record_view.xml',
        'views/visitas_view.xml',
        'views/main_menu.xml',
        'views/email_template.xml',
        'reports/reports.xml',   
        'reports/visitas_report.xml',   
    ],
    'assets': {
        'web.assets_backend': [
            '/control_visitas/static/src/xml/visitas_menu_template.xml',
            '/control_visitas/static/src/js/vistas_menu_action.js',
        ],
    },
    'auto_install': False,
    'application': True,
    'installable': True
}