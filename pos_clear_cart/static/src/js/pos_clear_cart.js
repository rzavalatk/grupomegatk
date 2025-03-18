odoo.define('pos_clear_cart.ClearCart', function (require) {
    'use strict';
    const { Gui } = require('point_of_sale.Gui');
    const PosComponent = require('point_of_sale.PosComponent');
    const { identifyError } = require('point_of_sale.utils');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('@web/core/utils/hooks');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    class ClearCart extends PosComponent {
        setup() {
            super.setup();
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            this.clear_button_fun();
        }
        clear_button_fun() {
            var order = this.env.pos.get_order();
            while (order.get_selected_orderline()) {
                order.remove_orderline(order.get_selected_orderline())
            }
        }
    }
    ClearCart.template = 'ClearCart';
    ProductScreen.addControlButton({
        component: ClearCart,
        condition: function () {
            return this.env.pos;
        },
    });
    Registries.Component.add(ClearCart);
    return ClearCart;
});

