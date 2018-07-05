# -*- coding: utf-8 -*-
{
    "name": "Modulo de campos personalizados",
    "author": "Romel Zavala",
    "description": "Campos megatk ",
    "category": "Sale",
    "depends": ["base",
        "crm",
       	"sale",
       	"purchase",
        "helpdesk"
	  ],
    "data": [
    	"views/sale_order_view.xml",
    	"views/purchase_order_view.xml",
    	"views/product_view.xml",
    	"views/res_partner_view.xml",
        "views/helpdesk_view.xml"
       #"views/crm_lead_views.xml",
 		#'security/groups.xml',
        #'security/ir.model.access.csv',
 		#"views/nota_debito_view.xml",
 		#"views/account_nota_debito.xml",
 		#"views/credit_note_inv_view.xml",
 		#"views/sale_order_view.xml",
        #"reports/cotizacion_arrendamiento.xml",
        #"reports/cotizacion_arrendamiento_view.xml"
        ],
	"auto_install": False,
	"installable": True,
}
