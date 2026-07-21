# -*- coding: utf-8 -*-
{
    "name": "Product Multi Website",
    "summary": "Permite asignar productos a multiples sitios web",
    "description": "Extiende productos para seleccionar varios sitios web y filtrar tienda por esa seleccion.",
    "version": "18.0.1.0.0",
    "category": "Website",
    "author": "MegaTK",
    "license": "LGPL-3",
    "depends": ["product", "website_sale"],
    "data": [
        "views/product_template_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
