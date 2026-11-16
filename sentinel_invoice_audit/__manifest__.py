{
    'name': 'Sentinel: auditoría de facturas de solo lectura',
    'version': '18.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['account', 'mail', 'base_automation'],
    'data': ['security/groups.xml', 'security/ir.model.access.csv', 'security/rules.xml'],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
