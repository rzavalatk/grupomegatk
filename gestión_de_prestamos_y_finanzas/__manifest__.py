{
    'name': 'Gestión de Préstamos y Finanzas',
    'version': '16.0',
    'category': 'Finance',
    'author': 'David Zuniga',
    'depends': ['base', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/main_menu_view.xml',
        'views/prestamo_views.xml',
        'views/cuota_views.xml',
        'views/cliente_views.xml',
        'views/contrato_views.xml',
        'views/garantia_views.xml',
        'views/solicitud_views.xml',
        'views/recurso_humano_views.xml',
        'views/usuario_views.xml',
        'data/prestamo_data.xml',
        'data/secuencia.xml',
        'report/prestamo_report.xml',
        'report/contrato_template.xml'
    ],
    'installable': True,
    'application': True,
}

