# -*- coding: utf-8 -*-
{
    'name': 'Legacy Web JS Shims',
    'summary': 'Compatibilidad para módulos JS antiguos (web.*) en Odoo 18',
    'version': '18.0.1.0.0',
    'author': 'Migración automática',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [],
    'assets': {
        # Módulo deshabilitado - migrar todos los módulos dependientes a Odoo 18 moderno
        # 'web.assets_backend': [
        #     'web_legacy_shims/static/src/js/legacy_shims.js',
        # ],
        # 'web.assets_frontend': [
        #     'web_legacy_shims/static/src/js/legacy_shims.js',
        # ],
    },
    'installable': True,
    'application': False,
    'auto_install': True,
}
