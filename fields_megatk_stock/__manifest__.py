# -*- coding: utf-8 -*-
{
    "name": "Modulo de campos personalizados Stock",
    "author": "Romel Zavala",
    "description": "Campos megatk, no facturar cero ni negativos(Cotización, Facturación)",
    "category": "Sale",
    "depends": ["base",
        "fields_megatk",
        "precios_megatk",
        "campos_referencia"
	  ],
    "data": [
        "views/stock_picking_view.xml"
        ,"views/product_view.xml"
         
        ],
	"auto_install": True,
	"installable": True,
}


