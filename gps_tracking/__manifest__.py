{
    'name': 'Rastreo GPS',
    'version': '1.0',
    'description': 'Modulo para rastreo GPS',
    'summary': 'Modulo para rastreo GPS',
    'author': 'Alexander Reyes',
    'license': 'LGPL-3',
    'category': 'uncategorized',
    'depends': [
        'base',
    ],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/gps_tracking_view.xml',
        'views/gps_tracking_main_menu.xml',
    ],
    
    'auto_install': False,
    'application': True,
    'installable': True
}