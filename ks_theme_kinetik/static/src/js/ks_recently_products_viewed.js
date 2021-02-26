odoo.define('ks_theme_kinetik.ks_products_recently_viewed', function (require) {
'use strict';

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;
    var QWeb = core.qweb;


     $(document).ready(function(){
     if ($('.ks_product_recent').length){
        var qweb_modal = ajax.loadXML('/ks_theme_kinetik/static/src/xml/modal.xml',QWeb)
        qweb_modal.then(function(){
        ajax.jsonRpc("/recently/products/viewed", 'call').then(function (data_list) {
            if (data_list["prods"]){
                $('.ks_product_recent').removeClass('d-none');
                var Html = $(QWeb.render('ks_theme_kinetik.ks_recently_product_views', {"products": data_list}));
                $('.ks_recent_product_data').html(Html[0]);
//                if ($('.ks_recent_carusols').children().length > 4){
                    $('.ks_recent_carusols').owlCarousel({
                        nav:true,
                        dots:false,
                        items : 4,
                        margin:15,
                        responsiveClass: true,
                        navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
                        responsive:{
                                0:{
                                    items:2,
                                },
                                600:{
                                    items:2,
                                },
                                1000:{
                                    items:4,
                                },
                                1400: {
                                   items:4,
                            }
                        }
                    });
//                }
            };
        });
        });
      }
      });


});