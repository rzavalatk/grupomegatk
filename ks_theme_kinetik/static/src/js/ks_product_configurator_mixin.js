odoo.define('ks_theme_kinetik.ProductConfiguratorMixin', function (require) {
    'use strict';

    var ProductConfiguratorMixin = require('sale.ProductConfiguratorMixin');
    var sAnimations = require('website.content.snippets.animation');
    sAnimations.registry.WebsiteSale.include({
        /**
         * Adds the stock checking to the regular _onChangeCombination method
         * @override
         */
        _onChangeCombination: function (){
            if (arguments[2].next_prod_url){
                $('.ks_next_pro').removeClass("d-none");
                $('.ks_next_pro').attr('href',arguments[2].next_prod_url);
            }
            if (arguments[2].prev_prod_url){
                $('.ks_previous_pro').removeClass("d-none");
                $('.ks_previous_pro').attr('href',arguments[2].prev_prod_url);
            }
            if(arguments[2].ks_description_post){
                $('.ks_show_description').html(arguments[2].ks_description_post)
                $('.ks_show_description').removeClass('d-none')
            }
            else{
                $('.ks_show_description').addClass('d-none')
                $('.ks_show_description').html(" ")
            }
            this._super.apply(this, arguments);
            $('.product-detail-carousel .ks_main .normal').attr('style','width: 100%!important;');
            if($('.ks_action_buttons').find('#add_to_cart').attr('Class').includes('disabled')){
                $('.add_cart_mobile').addClass('disabled out_of_stock');
            }
            else{
                $('.add_cart_mobile').removeClass('disabled out_of_stock');
            }
            $('.ks_action_buttons').find('#add_to_cart').removeClass('ks_out_of_stock');
            $('.add_cart_mobile').removeClass('ks_out_of_stock');
            var per_disc = ((arguments[2].list_price - arguments[2].price)/arguments[2].list_price)*100;
            if (per_disc > 0){
                $('.Percentage-offer').html('( ' + Math.floor(per_disc) + '% OFF)');
            }
            else{
                $('.Percentage-offer').html("")
            }
            if(arguments[2].default_code){
                $('.ks_prod_ref_01').html(" ");
                $('.ks_prod_ref_01').html(arguments[2].default_code)
            }
            else{
                $('.ks_prod_ref_01').siblings('.font-weight-bold').html(" ")
                $('.ks_prod_ref_01').html(" ");
            }
            var ks_img_vrnt = $('.ks_thumb').find('.ks_img_vrnt');
            if (ks_img_vrnt.length){
                $('.ks_thumb').find('.owl-stage').trigger('to.owl.carousel', ks_img_vrnt.attr('data-slide-to'));
                $('.ks_main').find('.owl-stage').trigger('to.owl.carousel', ks_img_vrnt.attr('data-slide-to'));
            }
            $('.product_detail_page').val(arguments[2].product_id)
            $('.product_quick_view').val(arguments[2].product_id)
            var seconds = arguments[2].seconds;
            if(seconds){
             $('.ks_product_timer_title').removeClass("d-none");
             $('.clock').removeClass("d-none");
             $('.ks_timer_box').removeClass("d-none");
             var clock = $('.clock').FlipClock(seconds, {
                            clockFace: 'DailyCounter',
                            countdown: true,
                });
             $('.clock').find('.flip-clock-label').remove();
            }
            else{
                $('.clock').addClass("d-none");
                $('.ks_timer_box').addClass('d-none');
                $('.ks_product_timer_title').addClass("d-none");
            }

        },
    });

     //Product_id change on variant selection in cart popover
    $(document).on('change','.ks_shop_product_popover [data-attribute_exclusions]',function(ev){
        ProductConfiguratorMixin['isWebsite'] = true
        ProductConfiguratorMixin.onChangeVariant(ev);
    });

    return ProductConfiguratorMixin;
});

odoo.define('ks_theme_kinetik.website_sale', function (require) {
'use strict';

    var website_sale = require('website_sale.website_sale');
    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.WebsiteSale.include({
        _updateProductImage: function () {
            this._super.apply(this, arguments);
            var product_length= $('.ks_multi_image_horizontal .ks_active_variant_image').length
            var ks_loop=true;
            if(product_length){
                if (product_length < 5){
                    ks_loop=false;
                }
            }
                else{
                product_length = $('.ks_vert_slider .ks_active_variant_image').length
                if (product_length < 5){
                    ks_loop=false;
                }
            }

            $('.ks_main').on('click', '.owl-next, .owl-prev', function (ev) {
                if($(ev.currentTarget).parents().eq(1).find('.ks_img_vrnt').length){
                    if($(ev.currentTarget).parents().eq(1).find('.center').children().attr('Class').includes('ks_img_vrnt')){
                        $($(ev.currentTarget).parents().find('.ks_thumb')).find('.owl-stage').trigger('to.owl.carousel', 0);
                    }
                    else{
                        var id = $(ev.currentTarget).parents().eq(1).find('.center').children().attr('data-oe-id');
                        $($(ev.currentTarget).parents().find('.ks_thumb')).find('.owl-stage').trigger('to.owl.carousel', id);
                    }
                }
                else{
                    var id = $(ev.currentTarget).parents().eq(1).find('.center').children().attr('data-oe-id');
                    $($(ev.currentTarget).parents().find('.ks_thumb')).find('.owl-stage').trigger('to.owl.carousel', id);
                }
            });


            $('.ks_thumb').on('click', '.owl-next, .owl-prev', function (ev2) {
                $($($(ev2.currentTarget).parent().siblings()[0]).find('.owl-item.active').children()).removeClass('active').addClass('ks-vs-img ks_active_variant_image')
                $($($(ev2.currentTarget).parent().siblings()[0]).find('.owl-item.active.center').children()).addClass('active')
            });

            var owl = $(document).find('.carousel-outer .owl-carousel');
            owl.on('dragged.owl.carousel', function(event) {
                var id = $('.ks_main').find('.center').children().attr('data-oe-id');
                $('.ks_thumb').find('.owl-stage').trigger('to.owl.carousel', id);
            })

            $('.ks_main').owlCarousel({
                loop:ks_loop,
                nav:true,
                dots:false,
                items:1,
                center:true,
                video:true,
                margin:5,
                navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
            });

            $('.ks_thumb').owlCarousel({
                loop:ks_loop,
                nav:true,
                center:true,
                dots:false,
                items : 5,
                margin: 5,
                navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
                responsiveClass: true,
                responsive:{
                    0:{
                        items: 3,
                    },
                    420: {
                        items: 4,
                    },
                    767: {
                        items: 3,
                    },
                    1200:{
                        items: 5,
                    }
                },
            });
            $('.ks_thumb').on('mousewheel', '.owl-stage', function (e) {
                $('.ks_thumb').trigger('next.owl');
                e.preventDefault();
            });
            var $easyzoom = $('.easyzoom').easyZoom();
        },

        _onChangeAttribute: function (ev) {
            if (!ev.isDefaultPrevented() && !$(ev.currentTarget).attr('class').includes('ks_price_input')) {
                ev.preventDefault();
                if($('.price_filter_list').hasClass('d-none')){
                    $("form.js_attributes").append('<input type="hidden" name="price_exp" value="False"/>');
                }
                $(ev.currentTarget).closest("form").submit();
            }
        },
    })
});

odoo.define('ks_theme_kinetik.website_sale_options_cart', function (require){
'use strict';

    var website_sale = require('website_sale_options.website_sale');
    var sAnimations = require('website.content.snippets.animation');
    var wSaleUtils = require('website_sale.utils');
    var core = require('web.core');
    var Qweb = core.qweb;
    var ajax = require('web.ajax');
    var CurrentProduct;

    sAnimations.registry.WebsiteSaleOptions.include({
        selector: '.oe_website_sale, .ks_dyn_snip',
        read_events: {
            'click #add_to_cart, .ks_add_to_cart_dynamic, #products_grid .product_price .a-submit': 'async _onClickAdd',
        },

        _onClickAdd: function (ev) {
            ev.preventDefault();
            CurrentProduct = $(ev.currentTarget);
            if(($(ev.currentTarget).parents('form').attr('class') !== undefined && !$(ev.currentTarget).parents('form').attr('class').includes('ks_optional')) || $(ev.currentTarget).parents('form').attr('class').includes('dyn_no_optional')){
                ev.stopPropagation();
                var product_custom_attribute_values = this.getCustomVariantValues($('#product_details .js_product'));
                var no_variant_attribute_values = this.getNoVariantAttributeValues($('#product_details .js_product'));
                var add_qty = parseInt($('.ks_quantity_panel').find('input[name=add_qty]').val())
                ajax.jsonRpc("/shop/product/cart/update", 'call', {'product_id': parseInt($(ev.currentTarget).siblings('input[name=product_id]').attr('value')),
                    'add_qty':add_qty,'product_custom_attribute_values': product_custom_attribute_values, 'no_variant_attribute_values': no_variant_attribute_values}).then(function (data) {
                    $('.my_cart_quantity').addClass('o_animate_blink');
                    $('.my_cart_quantity').text(data['qty'])
                    if($('.ks_mycart').length){
                        if($('.o_header_affix').attr('Class').includes('affixed') && $('.o_header_affix .fa-shopping-cart.nav__icons').length){
                            var target = $('.o_header_affix .fa-shopping-cart.nav__icons');
                        }
                        else{
                            var target = $('.fa-shopping-cart.nav__icons')
                        }
                    }
                    else{
                        if($('.o_header_affix').attr('Class').includes('affixed')){
                            var target = $('.o_header_affix #my_cart');
                        }
                        else{
                            var target = $('#my_cart')
                        }
                    }
                    if($(ev.target).parents('.ks-product-list-mode').length){
                        if($(CurrentProduct).attr('class').includes('shop_animate')){
                            if($(ev.target).parents('.ks-product-list-mode').attr('Class').includes("ks_shop_slider")){
                                var product_id = $(ev.target).parents('.oe_product_cart').find('.ks_product_template_id').val();
                                var Html = $(Qweb.render('ks_shop_new', {"product_id": product_id}));
                                $(ev.target).parents('.ks_shop_slider').children().find('.ks_prod_img').children().replaceWith(Html[0]);
                                wSaleUtils.animateClone(target, $(ev.target).parent().closest("form"), 25, 40);
                                ajax.jsonRpc("/shop/product/slider", 'call', {'product_id':product_id}).then(function (data){
                                    $(ev.target).parents('.ks_shop_slider').find('.ks_shop_product').replaceWith(data);
                                    $('.ks_shop_product_slider').carousel({
                                        interval: false,
                                    });
                                });
                            }
                            else{
                                wSaleUtils.animateClone(target, $(ev.target).parent().closest("form"), 25, 40);
                            }
                        }
                        else{
                            window.location.reload();
                        }
                    }
                    else if($('#product_details').length && !$('.ks_quick_prev_prod_detail').length){
                        if($(CurrentProduct).attr('class').includes('detail_animate')){
                            if($('.carousel-indicators').length){
                                 wSaleUtils.animateClone(target, $('.carousel-indicators').find('.owl-item.active.center'), 25, 40);
                            }
                            else{
                                 $('.owl-item.active .easyzoom .normal').attr('style','width: auto!important;');
                                 wSaleUtils.animateClone(target, $('.owl-item.active'), 25, 40);
                                 $('.owl-item.active .easyzoom .normal').attr('style','width: 100%!important;')
                            }
                        }
                        else{
                            window.location.href = "/shop/cart";
                        }
                    }
                    else if($('#product_details').length && $('.ks_quick_prev_prod_detail').length && $('.modal_shown.show').length){
                       $('.modal_pop_up').removeClass('d-none')
                       setTimeout(function(){ $('.modal_pop_up').addClass('d-none') }, 1500);
                    }
                    else{
                        wSaleUtils.animateClone(target, $(ev.target).parents('.product-card'), 25, 40);
                    }
                    if (data['display']){
                        CurrentProduct.addClass('ks_out_of_stock');
                    }
                });
            }
            else{
                return this._handleAdd($(ev.currentTarget).closest('form'));
            }
        },
    })
});