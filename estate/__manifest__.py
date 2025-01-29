{
    'name': "Real Estate",
    'summary': """Modulo estate de prueba""",
    'description': """Modulo estate de prueba...""",
    'author': "Alexander Reyes",
    "license": "LGPL-3",
    'category': 'Uncategorized',
    'version': '0.1',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/estate_property_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}