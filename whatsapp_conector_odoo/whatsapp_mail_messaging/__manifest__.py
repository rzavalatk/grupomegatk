# -*- coding: utf-8 -*-

{
    'name': 'Conector Odoo Whatsapp',
    'version': '16.0.1.1.0',
    'category': 'Extra Tools',
    'summary': """Odoo Whatsapp Conector Para Ventas, Factura, y el botón flotante en el sitio web""",
    'description': """Añadido opciones para el envío de mensajes de Whatsapp y Mails en barra de sistema, orden de venta, facturas, 
    portal web ver y compartir la url de acceso de los documentos utilizando compartir opción disponible en cada registro a través de 
    Whatsapp web..""",
    'author': 'Ing. David Zuniga',
    'website': "",
    'company': 'Kreativa por MegaTK',
    'maintainer': 'Departamento de TI Kreativa media',
    'depends': ['sale', 'account', 'website','sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/portal_whatsapp_view.xml',
        'views/sale_order_inherited.xml',
        'views/account_move_inherited.xml',
        'views/website_inherited.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'wizard/wh_message_wizard.xml',
        'wizard/portal_share_inherited.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "whatsapp_mail_messaging/static/src/js/whatsapp_button.js",
            "whatsapp_mail_messaging/static/src/js/mail_button.js",
            'whatsapp_mail_messaging/static/src/xml/whatsapp_button.xml',
            'whatsapp_mail_messaging/static/src/xml/mail_button.xml',
        ],
        'web.assets_frontend': [
            "whatsapp_mail_messaging/static/src/js/whatsapp_modal.js",
            "whatsapp_mail_messaging/static/src/js/whatsapp_icon_website.js",
            "whatsapp_mail_messaging/static/src/css/whatsapp.css"
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
