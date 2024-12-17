{
    'name': 'Asistencias y marcaciones',
    'version': '16.0.0',
    'summary': 'Administración de asistencia de empleados y conexión con un dispositivo de reloj de asistencia basado en la nube.',
    'description': """
        Administrador de Asistencia te permite gestionar y rastrear la asistencia de empleados mediante una conexión de API a dispositivos de reloj de asistencia basados en la nube.
    """,
    'category': 'Human Resources',
    'author': 'Ing David Zuniga - dalzubri.netlify.app',
    'contributors': ['Megatk'],
    'website': 'https://www.megatk.net',
    'license': 'LGPL-3',
    'company': 'Megatk',
    'maintainer': 'Megatk',
    'depends': ['base', 'hr'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/main_menu_view.xml',
        'views/asistencias_view.xml',
        'views/attendance_users_view.xml',
        'views/attendance_daily_view.xml',
        'views/conexion_view.xml',
        
    ],
    'qweb_template_dict': {
        'backend': [
            'static/src/js/conexion.js',
        ],
    },
    'installable': True,
    'application': True,
}
