{
    'name': 'Website Theme Install',
    'description': "Propose to install a theme on website installation",
    'category': 'Website',
    'version': '14.0',
    'data': [
        'views/assets.xml',
        'views/views.xml',
    ],
    'depends': ['website'],
    'qweb_template_dict': {
        'backend': [
            '/website_theme_install/static/src/less/website_theme_install.less',
        ],
    },
    'auto_install': True,
}
