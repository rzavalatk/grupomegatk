# -*- coding: utf-8 -*-
{
    "name": "Helpdesk Custom MegaTK",
    "summary": "Campos y vista condicional para tickets tecnicos",
    "description": "Personalizaciones de Helpdesk para mostrar campos solo en el area tecnica.",
    "author": "MegaTK",
    "category": "Services/Helpdesk",
    "license": "LGPL-3",
    "version": "18.0",
    "depends": ["helpdesk"],
    "data": [
        "views/helpdesk_team_views.xml",
        "views/helpdesk_ticket_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
