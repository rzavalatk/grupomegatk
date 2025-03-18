{
    "name": "POS Clear Cart",
    "author": "Alexander Reyes",
    "category": "Point of Sale",
    "summary": """Limpia el Carrito de Compra con un solo boton.""",
    "description": """Limpia el Carrito de Compra con un solo boton.""",
    "version": "16.0.1.1",
    "depends": ["base", "point_of_sale"],
    "data": [],
    "assets": {
        "point_of_sale.assets": ["bsi_pos_clear_cart/static/src/js/pos_clear_cart.js",
                                 "bsi_pos_clear_cart/static/src/xml/pos_clear_cart.xml",],
        
    },
    "images": ["static/description/Pos Clear Cart Banner.gif"],
    "qweb": [],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
    "auto_install": False,
}
