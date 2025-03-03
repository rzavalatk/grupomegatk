{
    'name': 'Localizacion',
    'version': '1.0',
    'description': 'Modulo de localizacion de repartidores',
    'summary': 'Modulo de localizacion de repartidores',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/localizacion_view.xml',  
        'views/main_menu.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}