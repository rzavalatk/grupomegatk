# -*- coding: utf-8 -*-
{
    "name": "Modulo de campos personalizados Stock",
    "author": "David Zuniga - MegaTK",
    "description": "Campos megatk, no facturar cero ni negativos(Cotización, Facturación)",
    "category": "Sale",
    "license": "LGPL-3",
    "depends": ["base",
        "fields_megatk",
        "precios_megatk",
        "campos_referencia"
	  ],
    "data": [
        "views/stock_picking_view.xml"
        #,"views/product_view.xml"
        ,"views/res_config.xml"
         
        ],
	"auto_install": True,
	"installable": True,
}


