odoo.define('website_add_to_cart_popup', function(require){
      "use strict";
    //Handling add to cart pop up on the shop page
    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var QWeb = core.qweb;
    var _t = core._t;
    var ch;
    var qweb_modal = ajax.loadXML('/ks_theme_kinetik/static/src/xml/modal.xml',QWeb);
    var wSaleUtils = require('website_sale.utils');
    var current_product;

    sAnimation.registry.add_to_cart_popup_template = sAnimation.Class.extend({
        selector: ".oe_website_sale",
        events: {
            'click .ks_variants .ks_variant_cart' : 'ks_onCartClick',
        },

        willStart:function(){
            return this._loadModalTemplate();
        },
        _loadModalTemplate:function(){
            return ajax.loadXML('/ks_theme_kinetik/static/src/xml/modal.xml',QWeb);
        },

        start: function () {
            var self = this;
            return this._super();
        },

        ks_onCartClick : function(e){
            e.preventDefault();
            if(!$('.ks-product-list-view').length){
                $(e.currentTarget).parent().closest('.ks_hover_data').css('transform',"translateY(-100%)");
            }
            current_product = e.currentTarget
            var ks_self = this;
            var ks_prod = $(e.currentTarget).data();
            var ks_prod_id = ks_prod.productId;
            if (!ks_prod_id){
                var ks_prod_id=ks_prod.productTemplateId;
            }

            ajax.jsonRpc("/shop/product_variant", 'call', {'product_id':ks_prod_id}).then(function (data) {
                $(e.currentTarget)
                    .popover({content: data[0], html: true, sanitize: false, placement: "right", trigger: "click"})
                    .popover('show')
                    .on('shown.bs.popover', function () {
                         $('.css_attribute_color').on("click",function(e){
                            $('.css_attribute_color').removeClass("active")
                            $(e.currentTarget).addClass("active");
                         });
                    })
            }.bind(ks_self));
        }
    });

    $(document).on("click",".ks_shop_product_popover .a-submit",function (e){
        e.stopPropagation();
        e.preventDefault();     // prevent page from scrolling up
        var product_custom_attribute_values = [];
        $('#product_details .js_product_popover').find('.variant_custom_value').each(function (){
            var $variantCustomValueInput = $(this);
            if ($variantCustomValueInput.length !== 0){
                product_custom_attribute_values.push({
                'attribute_value_id': $variantCustomValueInput.data('attribute_value_id'),
                'attribute_value_name': $variantCustomValueInput.data('attribute_value_name'),
                'custom_value': $variantCustomValueInput.val(),
                });
            }
        });
        var noVariantAttributeValues = [];
        var variantsValuesSelectors = [
            'input.no_variant.js_variant_change:checked',
            'select.no_variant.js_variant_change'
        ];
        $('#product_details .js_product_popover').find(variantsValuesSelectors.join(',')).each(function (){
            var $variantValueInput = $(this);

            if ($variantValueInput.is('select')){
                $variantValueInput = $variantValueInput.find('option[value=' + $variantValueInput.val() + ']');
            }

            if ($variantValueInput.length !== 0){
                noVariantAttributeValues.push({
                    'attribute_value_id': $variantValueInput.data('value_id'),
                    'attribute_value_name': $variantValueInput.data('value_name'),
                    'value': $variantValueInput.val(),
                    'attribute_name': $variantValueInput.data('attribute_name'),
                    'is_custom': $variantValueInput.data('is_custom')
                });
            }
        });

        ajax.jsonRpc("/shop/product/cart/update", 'call', {'product_id': parseInt($(e.currentTarget).siblings('input').attr('value')),
            'product_custom_attribute_values': product_custom_attribute_values,
            'no_variant_attribute_values': noVariantAttributeValues}).then(function (data) {
            $('.my_cart_quantity').addClass('o_animate_blink');
            $('.my_cart_quantity').text(data['qty']);
            var product_id = $(e.currentTarget).siblings('.product_template_id').attr('value')
            //Animation
            if($(e.currentTarget).attr('class').includes('popover_animate')){
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
                wSaleUtils.animateClone(target,  $('.ks_shop.ks_variants input[value=' + product_id + ']').parent().closest("form"), 25, 40);
            }
            $('.ks_shop.ks_variants input[value=' + product_id + ']').parent().find('.ks_hover_data').css('transform',"");
            $("[data-toggle='popover']").popover('hide')
            $("[data-toggle='popover']").popover('dispose')
        })
    });
});