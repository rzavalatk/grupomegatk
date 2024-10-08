# -*- coding: utf-8 -*-
##############################################################################

{
    'name': "Facturación Electrónica Honduras",
    'summary': """
        Regulación del SAR para regimene de facturación para autoimpresores agregado al pos
        """,
    'description': """
         Regulación del SAR para regimene de facturación para autoimpresores agregado al pos
    """,
    'author': 'Jiovanny Francisco Morales',
    'version': '1.0',
    'license': 'Other proprietary',
    'maintainer': '',
    'contributors': '',
    'category': 'Extra Tools',
    'depends': ['base', 'point_of_sale'],
    'data': [
        "views/vista_sar_pos.xml",
    ],
    'demo': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}