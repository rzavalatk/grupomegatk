{
    "name": "Flujo de caja proyectado",
    "summary": "Proyección operativa de cobros, pagos y disponible por empresa",
    "version": "18.0.9.0.0",
    "category": "Accounting/Accounting",
    "author": "Grupo Megatk",
    "license": "LGPL-3",
    "depends": ["account", "mail"],
    "data": [
        "security/flujo_caja_security.xml",
        "security/ir.model.access.csv",
        "data/flujo_caja_cron.xml",
        "views/flujo_caja_views.xml",
        "views/integracion_odoo_views.xml",
        "reports/portfolio_report.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "megatk_cash_flow_forecast/static/src/scss/cashflow_colors.scss",
        ],
    },
    "application": True,
    "installable": True,
}
