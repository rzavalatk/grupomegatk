odoo.define('ks_theme_website_wishlist', function (require) {
    'use strict'
    var ks_WishList = require('website_sale_wishlist.wishlist');
    var sAnimations = require('website.content.snippets.animation');
    var wSaleUtils = require('website_sale.utils');
    var core = require('web.core');
    var Qweb = core.qweb;
    var ajax = require('web.ajax');

    sAnimations.registry.ProductWishlist.include({
    selector: '.ks_main_tag',
     template: 'ks_shop_old',
     xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_main_slider.xml'],
    _addOrMoveWish: function (e) {
    var $def = this._super(e);
        $('#my_cart_2').removeClass('d-none');
        return $def
    },
    _updateWishlistView: function () {
        $('#my_wish').show();
        $('.my_wish_quantity').text(this.wishlistProductIDs.length);
    },
    _addNewProducts: function ($el) {
        var self = this;
        var productID = $el.data('product-product-id');
        if ($el.hasClass('o_add_wishlist_dyn')) {
            productID = $el.parent().find('.product_id').val();
            if (!productID) { // case List View Variants
                productID = $el.parent().find('input:checked').first().val();
            }
            productID = parseInt(productID, 10);
        }
        var $form = $el.closest('form');
        var templateId = $form.find('.product_template_id').val();
        // when adding from /shop instead of the product page, need another selector
        if (!templateId) {
            templateId = $el.data('product-template-id');
        }
        $el.prop("disabled", true).addClass('disabled');
        var productReady = this.selectOrCreateProduct(
            $el.closest('form'),
            productID,
            templateId,
            false
        );

        productReady.done(function (productId) {
            productId = parseInt(productId, 10);

            if (productId && !_.contains(self.wishlistProductIDs, productId)) {
                return self._rpc({
                    route: '/shop/wishlist/add',
                    params: {
                        product_id: productId,
                    },
                }).then(function () {
                    self.wishlistProductIDs.push(productId);
                    self._updateWishlistView();

                    if($('.ks_mycart').length){
                            if($('.o_header_affix').attr('Class').includes('affixed') && $('.o_header_affix .nav-item .fa-heart').length){
                                var target = $('.o_header_affix .nav-item .fa-heart');
                            }
                            else{
                                var target = $('.nav-item .fa-heart')
                            }
                        }
                        else{
                            if($('.o_header_affix').attr('Class').includes('affixed')){
                                var target = $('.o_header_affix #my_wish');
                            }
                            else{
                                var target = $('#my_wish')
                            }
                        }
                        if($el.parents('.ks-product-list-mode').length){
                            var prod = $el.closest('form');
                        }
                        else{
                            var prod = $el.parents('.product-card');
                        }

                    //if($el.parents('.ks-product-list-mode').length){
                        if ($el.parents('.ks-product-list-mode').length && $el.parents('.ks-product-list-mode').attr('Class').includes("ks_shop_slider")){
                            var product_id=$el.parents('.oe_product_cart').find('.ks_product_template_id').val();
                            var Html = $(Qweb.render('ks_shop_new', {"product_id": product_id}));
                            $el.parents().eq(2).find('.ks_prod_img').children().replaceWith(Html[0]);
                            wSaleUtils.animateClone(target,prod, 25, 40);
                            ajax.jsonRpc("/shop/product/slider", 'call', {'product_id':product_id}).then(function (data){
                                $el.parents().eq(2).find('.ks_shop_product').replaceWith(data);
                                $('.ks_shop_product_slider').carousel({
                                    interval: false,
                                });
                            });
                        }
                        else{
                         wSaleUtils.animateClone(target,prod, 25, 40);
                        }
                    //}
//                    else{
//                         wSaleUtils.animateClone(target,prod, 25, 40);
//                    }
                }).fail(function () {
                    $el.prop("disabled", false).removeClass('disabled');
                });
            }
        }).fail(function () {
            $el.prop("disabled", false).removeClass('disabled');
        });
    },
    });
});


