odoo.define('website_sale.ks_cart_popup', function (require) {
'use strict';

var sAnimations = require('website.content.snippets.animation');
var core = require('web.core');
var default_popup=require('website_sale.cart');
var _t = core._t;

var timeout;
sAnimations.registry.websiteSaleCartLink.include({
    selector: '#top_menu a[href$="/shop/cart"]',
    read_events: {
        'click': '_onMouseEnter',

    },
    _onMouseEnter: function (ev){
          var self = this;
//        clearTimeout(timeout);
        ev.preventDefault();

        $(this.selector).not(ev.currentTarget).popover('hide');
//        timeout = setTimeout(function () {
            if (!self.$el.is(':hover') || $('.mycart-popover:visible').length) {
                return;
            }
            $.get("/shop/cart", {
                type: 'popover',
            }).then(function (data) {
                self.$el.data("bs.popover").config.content = data;
                self.$el.popover("show");
                $('.mycart-popover .arrow').addClass('ks_cart_back_button');
                $('.ks_cart_back_button').attr('title','Close');
                $('body').addClass('js-no-scroll backdrop-shadow');
                $('.ks_cart_back_button').on('click', function () {
                    self._onMouseLeave();
                });
                $('#wrapwrap').on('click', function () {
                    self._onMouseLeave();
                });
            });
//        }, 0);
    },
     _onMouseLeave: function (ev) {
        var self = this;
        self.$el.popover('hide');
         $('body').removeClass('js-no-scroll backdrop-shadow');
    },
});
});
