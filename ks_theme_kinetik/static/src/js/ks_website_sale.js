odoo.define('ks_theme_website_sale_custom', function (require) {
    'use strict'
    var core = require('web.core');
    var _t = core._t;
    var ajax = require('web.ajax');
    var wSaleUtils = require('website_sale.utils');
    var sAnimations = require('website.content.snippets.animation');
    var ks_xmlDef = ajax.loadXML('/ks_theme_kinetik/static/src/xml/ks_product_grid.xml', core.qweb);
    /*
        This works only when the product loaded using ajax on shop page
    */
    $(document).on('slideStop', '#ks-price-filter', function (ev) {
     if($(".is_ks_load_ajax").length > 0){
         var ks_price_val = $("#ks-price-filter").val();
         $("#ks-selected_input_min").val(ks_price_val[0]);
         $("#ks-selected_input_min_hidden").val(ks_price_val[0]);
         $("#ks-selected_input_max").val(ks_price_val[1]);
         $("#ks-selected_input_max_hidden").val(ks_price_val[1]);
         $("form.js_attributes").submit();
        }
    });
    //Prevent the form submission and add data then fire ajax
    $(document).on('submit', 'form.js_attributes', function (ev) {
         if($(".is_ks_load_ajax").length > 0){
          $(".ks-loader").removeClass("d-none");
          ev.preventDefault(); // Disable form submition in editable mode
          var ks_filters = $(this).serializeArray()
          var cate_activated_filter = $(".ks-active-category");
          var ks_category_text;
          var ks_price_val = $("#ks-price-filter").val();
          var ks_order = $('.ks-active-sorting').find(".ks_sortable").val();
          var ks_ajax;
	      var active=false;


          $("#ks-selected_input_min").val(ks_price_val[0]);
          $("#ks-selected_input_min_hidden").val(ks_price_val[0]);
          $("#ks-selected_input_max").val(ks_price_val[1]);
          $("#ks-selected_input_max_hidden").val(ks_price_val[1]);
          if (cate_activated_filter){
            ks_category_text = cate_activated_filter.text().trim();
          }
          _.each(ks_filters,function(filter){
            if(filter['name'] === 'min'){
                filter['value'] = ks_price_val[0];
            }
            if(filter['name'] === 'max'){
                filter['value'] = ks_price_val[1];
            }
          })
          if(ks_order !== undefined){
              ks_filters.push({"name":"order", "value":ks_order})
          }
          ks_filters.push({"name":"category", "value":ks_category_text})
//          if(this.active) { ks_ajax.abort(); }
//          this.active=true;
          ks_xmlDef.then(function(){
          ks_ajax =  ajax.jsonRpc("/shop2/products", 'call', {'filters':ks_filters}).then(function (values) {
                $(".ks-loader").addClass("d-none");
                $("#products_grid").empty().append(core.qweb.render('ks_theme_kinetik.ks_product_grid', {  "products": values}));
                $(".breadcrumb").replaceWith(core.qweb.render('ks_theme_kinetik.ks_breadcrumb', {  "products": values}));
                $(".pagination").html(core.qweb.render('ks_theme_kinetik.ks_theme_pagination', {  "products": values}));
                active=false;
            });
         });
     }
     else{
        _.each($(".products_pager .pagination"),function(pager){
               $(pager).removeClass("d-none");
           });
        return true;
     }
    });

    //Custom Pager values
    $(document).on('click', '.ks-pager-items, .ks-pager-prev, .ks-pager-nxt', function (ev) {
        var ks_pager_offset = $(this).text().trim();
        $(".ks-loader").removeClass("d-none");
        var ks_filters = $('form.js_attributes').serializeArray();
        var ks_order = $('.ks-active-sorting').find(".ks_sortable").val()
        var active_page  = parseInt($('.ks_active_pager').text().trim())
        if($(this).hasClass("ks-pager-nxt")){
            if(! $.isNumeric( ks_pager_offset ) ){
             ks_pager_offset = active_page + 1;
            }
            else{
              ks_pager_offset = active_page;
            }
        }
        if($(this).hasClass("ks-pager-prev")){
            if(active_page > 1){
                ks_pager_offset = active_page - 1;
            }
            else{
              ks_pager_offset = 1;
            }
        }
        ks_filters.push({"name": "num","value": ks_pager_offset});
        _.each($(".ks-pager-item"),function(activated_category){
                 $(activated_category).removeClass("ks-active-category");
        });
         if(ks_order !== undefined){
              ks_filters.push({"name":"order", "value":ks_order})
         }
        ajax.jsonRpc("/shop2/products", 'call', {'filters':ks_filters}).then(function (values) {
            $(".ks-loader").addClass("d-none");
            $("html, body").animate({ scrollTop: 0 }, "fast");
            $("#products_grid").empty().append(core.qweb.render('ks_theme_kinetik.ks_product_grid', {  "products": values}));
            $(".breadcrumb").replaceWith(core.qweb.render('ks_theme_kinetik.ks_breadcrumb', {  "products": values}));
            $(".pagination").html(core.qweb.render('ks_theme_kinetik.ks_theme_pagination', {  "products": values}));

        });
        return false;
    });

    //Sorting with ajax filters
    $(document).on('click', ' div.dropdown_sorty_by .dropdown-item', function (ev) {
        if($(".is_ks_load_ajax").length > 0){
            $(".ks-loader").removeClass("d-none");
            ev.preventDefault(); // Disable form submition in editable mode
            var ks_filters = $('form.js_attributes').serializeArray()
            var ks_order = $(this).find(".ks_sortable").val();
            var ks_cate  = $(".ks-active-category").text().trim();
            var ks_brnds = $('input[name="brnd"]:checked')[0];
            _.each($(".ks-active-sorting"),function(activated_category){
                     $(activated_category).removeClass("ks-active-sorting");
                });
             $(this).addClass("ks-active-sorting");
            if(ks_brnds){
                _.each(ks_brnds,function(brnd){
                     ks_filters.push({"name": "attrib","value": brnd.defaultValue})

                });
            }
            ks_filters.push({"name":"category", "value":ks_cate})
            if(ks_order !== undefined){
              ks_filters.push({"name":"order", "value":ks_order})
            }
            ajax.jsonRpc("/shop2/products", 'call', {'filters':ks_filters}).then(function (values) {
                    $(".ks-loader").addClass("d-none");
                    $("#products_grid").empty().append(core.qweb.render('ks_theme_kinetik.ks_product_grid', {  "products": values}));
                    $(".breadcrumb").replaceWith(core.qweb.render('ks_theme_kinetik.ks_breadcrumb', {  "products": values}));
                    $(".pagination").html(core.qweb.render('ks_theme_kinetik.ks_theme_pagination', {  "products": values}));

            });
        }
    });

    //Handling with categories filters
    $(document).on('click', '.ks-filter-outer li.nav-item a.nav-link', function (ev) {
        if($(".is_ks_load_ajax").length > 0){
            $(".ks-loader").removeClass("d-none");
            ev.preventDefault(); // Disable form submition in editable mode
            var ks_filters = $('form.js_attributes').serializeArray()
            var ks_order = $('.ks-active-sorting').find(".ks_sortable").val();
            _.each($(".ks-active-category"),function(activated_category){
                 $(activated_category).removeClass("ks-active-category");
            });
            $(this).addClass("ks-active-category");
            $(this).css("ks-active-category");
            var ks_cate = $($(this).context).text().trim();
            var ks_brnds = $('input[name="brnd"]:checked')[0];
            if(ks_brnds){
            _.each(ks_brnds,function(brnd){
                 ks_filters.push({"name": "attrib","value": brnd.defaultValue})

            });
            }
            if(ks_order !== undefined){
             ks_filters.push({"name":"order", "value":ks_order})
            }
            ks_filters.push({"name":"category", "value":ks_cate})
            ajax.jsonRpc("/shop2/products", 'call', {'filters':ks_filters}).then(function (values) {
                $(".ks-loader").addClass("d-none");
                $("#products_grid").empty().append(core.qweb.render('ks_theme_kinetik.ks_product_grid', {  "products": values}));
                $(".breadcrumb").replaceWith(core.qweb.render('ks_theme_kinetik.ks_breadcrumb', {  "products": values}));
                _.each($(".pagination"),function(page){
                    $(page).html(core.qweb.render('ks_theme_kinetik.ks_theme_pagination', {  "products": values}));
                });
            });
        }
        else{
            _.each($(".products_pager .pagination"),function(pager){
                 $(pager).removeClass("d-none");
            });
        }
     });
     $(document).on("show.bs.dropdown","li#customize-menu",function(ev){
         var currentTime = new Date().getTime();
         while (currentTime + 500 >= new Date().getTime()) {

         }
     });

    //To avoid drop down getting closed while clicking on tabs
    $(document).on('click', '#wrapwrap .dropdown-menu', function (e) {
      e.stopPropagation();
    });

//    $(document).ready(function(){
//     var seconds=$('.product_timer').find('input').val()
//     var clock = $('.clock').FlipClock(seconds, {
//        clockFace: 'DailyCounter',
//                    countdown: true,
//        });
//    });

//   handle the count of product
//    $(document).on('click', '.ks_hover_data .product_price .a-submit', function (ev) {
//         var product_id=$(ev.currentTarget).parents(".product_price").find("[name='product_id']").val();
//         if(product_id){
//         ajax.jsonRpc("/cart/count/update", 'call', {'product_id':product_id}
//                    ).then(function(list_data){
//                            var quantity=list_data
//                            if(quantity){
//                            if ($('#my_cart_2').length){
//                            $('#my_cart_2').removeClass('d-none');
//                            $('.my_cart_quantity').addClass('o_animate_blink');
//                            $('.my_cart_quantity').text(quantity)
//                            wSaleUtils.animateClone($('#my_cart_2'), $(ev.target).parent().closest("form"), 25, 40);
//                            }
//                            else{
//                            $('#my_cart').removeClass('d-none');
//                            $('.my_cart_quantity').addClass('o_animate_blink');
//                            $('.my_cart_quantity').text(quantity)
//                             wSaleUtils.animateClone($('#my_cart'), $(ev.target).parent().closest("form"), 25, 40);
//                             }
//                         }
//                    }.bind(this));
//               return false;
//                }
//            });

        $(document).on('click', '.ks_modal_optional', function (ev) {
                var val = $('.quantity').val();
                $(ev.currentTarget).parent().find('.mobile-add').attr("value",val)
                var product_id=$(ev.currentTarget).attr('data-product-product-id')
                var product_template_id=$(ev.currentTarget).attr('data-product-template-id')
                  ajax.jsonRpc("/details/cart/update", 'call', {'product_id':product_id,'template_id':product_template_id}
                  ).then(function(data){
                  if(data){
                $('#product_details').addClass('ks_cart_on_product_detail');
                }
                })
        })
});

//$('.quantity').val()
//$(ev.currentTarget).prev().attr("value",$('.quantity').val())