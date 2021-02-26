odoo.define('ks_ecommerce_theme.ks_load_more_products', function (require) {
'use strict';
    var ajax = require('web.ajax');
    var flag=0;
    var count=1;
    var doc_height;
    var elem_height;

    $( document ).ready(function() {
        if($(document).find('.product_load_more').length){
             elem_height= $('.ks_all_product').outerHeight();
             if($(document).find('.auto_load_more').length){
                $('.auto_load_more').addClass('d-none')
             }
         }
    });
    //   automatic load
    $(window).on('scroll', function() {
        if(flag<=1){
            if($('.ks-product-list-view').length)
                elem_height= $('.ks-product-list-view').outerHeight();
            else
                elem_height= $('.ks_all_product').outerHeight();
            flag+=1;
        }
        if($(document).find('.auto_load_more').length){
            if ($(window).scrollTop() >= (((elem_height)*count) - window.innerHeight)) {
                count=count+1;
                $(document).find('.product_load_more').click()
            }
        }
    });

    //   this is for load more button on product grid
    $(document).on('click','.product_load_more',function(ev){
        $("body").removeAttr("style")
        $(ev.currentTarget).addClass('disabled')
        var offset=$('.page_number').val();
        var ppg=$('.product_per_page').val();
        var load_class = $($('#products_grid').children().last()).clone(true).attr('class');
        var active_page=$($('.page-item.active')[0]).text().trim();
        var ks_filters = $('form.js_attributes').serializeArray();
        var ks_order = $('.ks_sort_per_page').val();
        var ks_cate=$('.category_active').val();
        var min_price=$("#ks-selected_input_min_hidden").val();
        var max_price=$("#ks-selected_input_max_hidden").val();
        var ks_search=$('input[name=search]').val();
        if(load_class.includes("ks_all_product")){
          load_class = $($('.ks-product-list')).attr("class");
        }
        ks_filters.push({"name": "offset","value": offset});
        ks_filters.push({"name":"load_class", "value":load_class})
        var ks_brnds = $('input[name="brnd"]:checked');
        if(ks_brnds){
            _.each(ks_brnds,function(brnd){
                ks_filters.push({"name": "attrib","value": brnd.defaultValue})
            });
        }
        if(ks_search !== undefined){
            ks_filters.push({"name":"search_2", "value":ks_search})
        }
        if(min_price !== undefined){
            ks_filters.push({"name":"min_price", "value":min_price})
        }
        if(max_price !== undefined){
            ks_filters.push({"name":"max_price", "value":max_price})
        }
        if(ks_order !== undefined){
            ks_filters.push({"name":"order", "value":ks_order})
        }
        if(ks_cate !== undefined){
         ks_filters.push({"name":"category", "value":ks_cate})
        }
        $('.page_number').val(parseInt(offset)+parseInt(ppg));
        ajax.jsonRpc("/shop/load/more", 'call', {'filters':ks_filters}).then(function (values) {
            if (values["list_view"]){
                if(values["page_count"]==1){
                    $("body").css({"position": "sticky", "overflow": "hidden"});
                    $("div.oe_website_sale div#products_grid").append(values.template);
                    $('.product_load_more').addClass('d-none');
                    $("div.oe_website_sale div#products_grid").append('<div class="d-none ks_no_more_prod"><p>No More Products</p></div>');
                    $("body").css({"position": "static", "overflow": "auto"});
                }
                else{
                    $("body").css({"position": "sticky", "overflow": "hidden"});
                    $("div.oe_website_sale div#products_grid").append(values.template);
                    $('.product_load_more').removeClass('disabled');
                    $("body").css({"position": "static", "overflow": "auto"});
                }
            }
            else{
                if(values["page_count"]==1){
                    $("body").css({"position": "sticky", "overflow": "hidden"});
                    $("div.oe_website_sale div#products_grid .ks_all_product").append(values.template);
                    $('.product_load_more').addClass('d-none');
                    $("div.oe_website_sale div#products_grid").append('<div class="d-none ks_no_more_prod"><p>No More Products</p></div>');
                    $("body").css({"position": "static", "overflow": "auto"});
                }
                else{
                    $("body").css({"position": "sticky", "overflow": "hidden"});
                    $("div.oe_website_sale div#products_grid .ks_all_product").append(values.template);
                    $('.product_load_more').removeClass('disabled');
                    $("body").css({"position": "static", "overflow": "auto"});
                }
            }
            if($('.hide_no_product_found').length){
                if($('.ks-product-list').length){
                    $('.hide_no_product_found').addClass('d-none')
                }
             }
        })
    })

});