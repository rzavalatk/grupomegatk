odoo.define('ks_ecommerce_theme.main', function (require) {
    'use strict';
    var ajax = require('web.ajax');

    $(document).ready(function(){

        var ks_head = $("head");
        var $style = $("<style>")
//                    $("#my_cart").remove();
         ajax.jsonRpc("/new_snippets/styles", 'call', {}).then(function (data) {
            _.each(data,function(e){
                $style.append(data.snippets_css);
            });
            ks_head.append($style);
        });
         $("#ex2").slider({});

         // Without JQuery
//                            var slider = new Slider('#ex2', {});

        //Because of this comparision works on homepage
        $('#wrapwrap.homepage main').addClass("oe_structure oe_empty oe_website_sale");
        var pathname = window.location.pathname;
        var parts = pathname.split("/");
        var last_part = parts[parts.length-1];
        //Removing cart page from the payment pages
        if(last_part==="payment" || last_part==="checkout" || last_part==="address" ){
            $("#my_cart_2").remove();
            }
        $(document).on('click', '.ks-vs-img',function(ev){
            var id = $(ev.currentTarget).attr('data-slide-to')
            $(ev.currentTarget.parentElement).siblings().find('.active').removeClass('active')
            $($(ev.currentTarget)).trigger('to.owl.carousel',id).addClass('active')
            $($(ev.currentTarget).parents().find('.ks_main')).find('.owl-stage').trigger('to.owl.carousel',id).addClass('active');
        });
    });
});

