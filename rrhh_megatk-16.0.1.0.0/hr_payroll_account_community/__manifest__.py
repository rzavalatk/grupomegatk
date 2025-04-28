# -*- coding: utf-8 -*-

{
    'name': 'Odoo16 Contabilidad de nómina',
    'category': 'Recursos humanos',
    'summary': """
          Sistema de nómina genérico integrado con contabilidad, codificación de gastos, codificación de pagos y gestión de contribuciones de la empresa.
    """,
    'description': """
          Sistema de nómina genérico integrado con contabilidad, codificación de gastos, codificación de pagos y gestión de contribuciones de la empresa.""",
    'version': '16.0.1.1.0',
    'author': 'Odoo SA,Cybrosys Techno Solutions, Ing. David Zuniga',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Megatk',
    'website': 'https://www.megatk.net',
    'depends': ['hr_payroll_community', 'account'],
    'data': ['views/hr_payroll_account_views.xml'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
