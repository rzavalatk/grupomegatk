odoo.define('ks_ecommerce_theme.product_multi_slider_base_multitab', function(require) {
    "use strict";

    var session = require('web.session');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var animation = require('website.content.snippets.animation');
    var core = require('web.core');
    var website = require('website.utils');
    var _t = core._t;
    var qweb = core.qweb;

    var WebsiteSaleProductSlider = Widget.extend({
        events: {},

        init: function(parent, id) {
            this._super(parent);
        },

        start: function() {
              this._super();

        }
    });

    animation.registry.website_sale_mutitab_product_slider_1 = animation.Class.extend({
        selector: ".ks_product_slider_multiple_tab",
        widget: null,
        template: 'snippet_multi_tab',
        xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_multitab_slider_inside.xml'],

        ks_handleRecords:function(data,$target){
                var $inner_temp = $(qweb.render('snippet_multi_tab', {
                 "products": data,
               }));
               if($target){
                    $inner_temp.appendTo($target.empty());
                   _.each($(".tabs-product-owl"),function(slider){
                          $(slider).owlCarousel({
                              items:data.ks_items_per_slide,
                              autoplay:data.ks_auto_slide,
                              margin:14,
                              rtl:data.rtl,
                              speed:data.ks_Speed,
                              loop:data.ks_loop,
                              nav:data.ks_nav_links,
                              autoplayHoverPause: true,
                              navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
                              responsiveClass: true,
                              responsive:{
                                    0:{
                                        items: 2,
                                        dots: true,
                                        margin:0,
                                    },
                                    960:{
                                        items: 3,
                                        dots: true
                                    },
                                    1200:{
                                        items: data.ks_items_per_slide,
                                    }
                                },

                           })
                   }.bind(data));
               }
        },
        start: function(slider_id,ks_self_recived) {
            var ks_self = this;

            if(ks_self_recived !== undefined){
                ks_self = ks_self_recived;
                ks_self.$target.attr('data-id', slider_id);
                this.$el = ks_self_recived.$el;
                this.$target = ks_self_recived.$target;
                this.data = ks_self_recived.data;
                this.overlay = ks_self_recived.overlay;
            }
            var $target = ks_self.$target;
            var id = ks_self.$target.attr('data-id');

            if (!id) {
                return;
            }

            ajax.jsonRpc("/multitab/product/data", 'call', {"snippet_name":"slider","id":id}).then(function (data) {
                    this.ks_handleRecords(data,$target);
            }.bind(this));

        },
        stop: function() {
            this.widget.destroy();
        }
    });

});