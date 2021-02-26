odoo.define('website_product_quick_preview', function(require){
  "use strict";
    //Handling quick preview on the shop page
     var sAnimation = require('website.content.snippets.animation');
     var ajax = require('web.ajax');
     var core = require('web.core');
     var QWeb = core.qweb;
     var OptionalProductsModal = require('sale.OptionalProductsModal');
     var _t = core._t;
     var ch;
     var qweb_modal = ajax.loadXML('/ks_theme_kinetik/static/src/xml/modal.xml',QWeb);
    sAnimation.registry.product_quick_preview_template = sAnimation.Class.extend({
       selector: ".ks_main_tag",
       template: 'product_quick_preview_template',
        events: {
            'click .o_quick_view' : 'ks_onPreviewClick',
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
         //handles the click on the quick preview button on shop page
         ks_onPreviewClick : function(e){
            var ks_self = this;
            var ks_prod = $(e.currentTarget).data()
            var ks_prod_id = ks_prod.productId
            if (!ks_prod_id){
                var ks_prod_id=ks_prod.productTemplateId
                }
            var modal_html =  $(QWeb.render('ks_theme_kinetik.products_modal', {}));
            $('#product_modal').html("")
            ajax.jsonRpc("/shop/product", 'call', {'product_id':ks_prod_id}).then(function (data_list) {
            if(data_list[1]==0 || $(e.currentTarget).parents('.ks_dyn_snip').length){
                var data=data_list[0];
                $('.oe_website_sale div:first').append(modal_html);
                $('#product_modal').html(data);
                $('#product_quick_preview_Modal').modal('show');
                 $("#product_quick_preview_Modal").modal({
                    show: 'true'
                });
                if($(e.currentTarget).parents('.ks_dyn_snip').length){
                    $(document).find('#product_quick_preview_Modal').find('form.ks_prod_form').addClass('dyn_no_optional');
                }
            }
            else{
                $(e.currentTarget).parent().find('.a-submit').click()
            }
            if(data_list[2]['per_desc'] > 0){
                $('.ks_quick_prev_prod_detail .Percentage-offer').html(' ( ' + Math.floor(data_list[2]['per_desc']) + '% OFF)');
            }
//.......................................for slider of quick preview......................................................................
            var quick_pre_product_length = $('.ks_thumb .ks_active_variant_image').length
            var ks_loop=true;
            if (quick_pre_product_length<5){
                ks_loop=false;
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
                margin:5,
                video:true,
                navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
            });

            $('.ks_thumb').owlCarousel({
                loop:ks_loop,
                nav:true,
                center:true,
                dots:false,
                items:5,
                navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
            });
        }.bind(ks_self));
        }
    });

});

