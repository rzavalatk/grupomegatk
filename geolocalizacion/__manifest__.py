{
    'name': 'Geolocalizacion',  
    'version': '1.0',
    'description': 'Geolocalizacion',
    'summary': 'Geolocalizacion de los usuarios',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base', 
        'hr'
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/main_menu.xml',
    ],
    'auto_install': False,
    'application': True,
    'installable': True
}