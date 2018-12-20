# -*- coding: utf-8 -*-
{
    "name": "Modulo de campos personalizados Stock",
    "author": "Romel Zavala",
    "description": "Campos megatk ",
    "category": "Sale",
    "depends": ["base",
        "fields_megatk",
        "precios_megatk"
	  ],
    "data": [
        "views/stock_picking_view.xml"
         ,"views/product_view.xml"
         ,"views/res_users_view.xml"
        ],
	"auto_install": False,
	"installable": True,
}
