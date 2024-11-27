{
    'name': 'SQL Server Connection',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Example of SQL Server connection using pymssql',
    'author': 'Tu Nombre',
    'depends': ['base'],
    'installable': True,
    'application': False,
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/sql_connection_view.xml',
    ],
    "external_dependencies": {"python": [
        "pymssql",
    ], "bin": []},
}
