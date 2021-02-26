odoo.define('ks_ecommerce_theme.ks_footer', function (require) {
'use strict';

    var ajax = require('web.ajax');
    var ProductConfiguratorMixin = require('ks_theme_kinetik.ProductConfiguratorMixin');
    var wSaleUtils = require('website_sale.utils');
    var core = require('web.core');
    var _t = core._t;
    var ks_p_id;

    $(document).ready(function(){

        $(document).on('mouseover','.product-detail-carousel .ks_main .center .normal',function(e){
            $(e.currentTarget).attr('style','width: auto!important;');
        });

        $(document).on('mouseout','.product-detail-carousel .ks_main .center .normal',function(e){
            $(e.currentTarget).attr('style','width: 100%!important;')
        });

        $('.ks-search-clear').on("click",function(e){
            location.href='/shop';
        })

        $(document).on('click','.ks_close_popup',function(e){
            $("[data-toggle='popover']").popover('hide')
            if($('.popover').length){
                $('.ks_hover_data').css('transform',"");
                $("[data-toggle='popover']").popover('dispose')
            }
        });

        $('.js_sale').on("click",function(e){
            $("[data-toggle='popover']").popover('hide')
            if($('.popover').length){
                $('.ks_hover_data').css('transform',"");
                $("[data-toggle='popover']").popover('dispose')
            }
        });

          //Product_id change on variant selection in cart popover
        $(document).on('change','.ks_shop_popup',function(ev){
            ajax.jsonRpc("/Combination/Variant/Id", 'call', {'product_id': parseInt($('.ks_shop_popup').val())}).then(function (data) {
                if (data['display']){
                    $(ev.currentTarget).parent().find("#add_to_cart").addClass('disabled');
                }
                else{
                    $(ev.currentTarget).parent().find("#add_to_cart").removeClass('disabled');
                }
                if($(ev.currentTarget).parents('.js_product_popover').attr('class').includes('css_not_available')){
                    $(ev.currentTarget).parents('.js_product_popover').children('#add_to_cart').addClass('disabled');
                }
            });
        });

//.......................................for shop page product slider..................................................

        $('.ks_shop_product_slider').carousel({
            pause: true,
            interval: false,
        });

        $(document).on("mouseover",".ks_shop_product_slider",function (e){
            $(e.currentTarget).find('.carousel-indicators').removeClass('d-none')
            $(e.currentTarget).carousel('dispose')
            $(e.currentTarget).carousel({
            });
            $('#ks_main_for_hover_slider').on('slid.bs.carousel', function () {
//                if($(this).find('.carousel-inner').children('.ks_mouse_leave').length == 1){
//                    $(this).find('.carousel-inner').children('.carousel-item.active').removeClass('active');
//                    $(this).find('.carousel-inner').children('.ks_mouse_leave').attr('class','carousel-item active')
//                }
            })
        });

        $(document).on("mouseleave",".ks_shop_product_slider",function (e){
           $(e.currentTarget).find('.carousel-indicators').addClass('d-none')
           $(e.currentTarget).carousel('dispose')
           $(e.currentTarget).carousel({
               interval: false,
           });
        });

        $(document).on("touchstart",".ks_shop_product_slider",function (event){
            var xClick = event.originalEvent.touches[0].pageX;
            $(this).one("touchmove", function(event){
                var xMove = event.originalEvent.touches[0].pageX;
                if( Math.floor(xClick - xMove) > 5 ){
                    $(this).carousel('next');
                }
                else if( Math.floor(xClick - xMove) < -5 ){
                    $(this).carousel('prev');
                }
            });
            $(".ks_shop_product_slider").on("touchend", function(){
                $(this).off("touchmove");
            });
        });

//........................................end of shop page product slider.................................................................

        $('.o_product_info').on("click",function(e){
            $("#product_quick_preview_Modal").modal('show');
        });

        $('.product-select').on('click',function(e){
            $('.ks_text').val(e.target.text)
            var ks_order = $('.ks_sort_per_page').val();
            if (ks_order !== undefined){
                $("form.js_attributes").append('<input type="hidden" name="order" value="'+ks_order+'"/>').submit();
            }
            else{
                $("form.js_attributes").submit();
            }
        })


        $(document).on('click', ' div.dropdown_sorty_by .dropdown-item', function (ev) {
            var order=$(ev.currentTarget).find('input').val()
            $('.ks_sort_per_page').val(order);
        })

        $(document).ready(function(){
            var brand=$('#ksBrandContainer').find('.active').text().trim();
            if ($('#o_shop_collapse_category')){
                if ( !$('#o_shop_collapse_category').find('li a.active').hasClass('o_not_editable')){
                    $('#o_shop_collapse_category').find('li a.active').addClass('ks_active')
                }
            }
            var ks_cate=$('.ks_active').text().trim();

            _.each($('input[name="brnd"]:checked'), function(ev) {
                if (ev){
                    $('.filter-selectedFilterContainer').removeClass('d-none');
                    $('.brand_filter_list').removeClass('d-none');
                    $('.brand_filter_list').append('<div class="ks_var_filter_list '+$(ev).val()+'"></div>')
                    $('.brand_filter').removeClass('d-none');
                    $('.'+$(ev).val()).append($(ev).parent().html());
                    $('.'+$(ev).val()).append('<span class="remove_brand_filter fa fa-times"></span>')
                    $('.'+$(ev).val()).find('input').addClass('d-none')
                }
            })
            _.each($('input[name="attrib"]:checked'), function(ev) {
                if (ev){
                    $('.filter-selectedFilterContainer').removeClass('d-none');
                    $('.variants_filter_list').removeClass('d-none');
                    $('.variants_filter_list').append('<div class="ks_var_filter_list '+$(ev).val()+'"></div>')
                    $('.variants_filter').removeClass('d-none');
                    $('.'+$(ev).val()).append($(ev).parent().html());
                    if ($(ev).attr('title')){
                        var color=$(ev).attr('title');
                    //                      $('.'+$(ev).val()).append('<label>'+color+'</label>');
                    }
                    $('.'+$(ev).val()).append('<span class="remove_variant_filter fa fa-times"></span>')
                    $('.'+$(ev).val()).find('input').addClass('d-none')
                }
            })
            if ($('select[name="attrib"]  option:selected').val()!=""){
                _.each($('select[name="attrib"]  option:selected'), function(ev) {
                    if(ev){
                        $('.filter-selectedFilterContainer').removeClass('d-none');
                        $('.variants_filter_list').removeClass('d-none');
                        $('.variants_filter_list').append('<div class="ks_var_filter_list '+$(ev).val()+'"></div>');
                        $('.variants_filter').removeClass('d-none');
                        $('.'+$(ev).val()).append('<label>'+$(ev).text()+'</label>')
                        $('.'+$(ev).val()).append('<span class="remove_variant_filter fa fa-times"></span>')
                    }
                })
            }
            if (ks_cate){
                $('.filter-selectedFilterContainer').removeClass('d-none');
                $('.filterList').removeClass('d-none');
                $('.filterList').append('<span class=ks-selected-items >'+ks_cate+'</span> <a class="remove_filter fa fa-times"><a/>')
            }
            var selected_min=parseFloat($('#ks-selected_input_min_hidden').val())
            var selected_max=parseFloat($('#ks-selected_input_max_hidden').val())
            var min=parseFloat($('#ks-price-filter').attr('data-slider-min'));
            var max=parseFloat($('#ks-price-filter').attr('data-slider-max'));
            if ($('.ks_filter_button').length){
                if ($('#ks-price-filter').attr('data-slider-min')==undefined){
                    min=0
                }
                if ($('#ks-price-filter').attr('data-slider-max')==undefined){
                    max=0
            }}
            if (((selected_min)>min | (selected_max)<max) && $('#ks-price-filter').length !=0){
                $('.filter-selectedFilterContainer').removeClass('d-none');
                $('.price_filter_list').removeClass('d-none');
                $('.price_filter_list').append('<span class=ks-selected-items>'+selected_min+' - '+selected_max+'</span><a class="remove_price_filter fa fa-times"><a/>')
            }
            if ($('.dropdown_sorty_by button.dropdown-toggle .sort_span').hasClass('sorting_active')){
                var ks_order=$('.dropdown_sorty_by button.dropdown-toggle').find('span').text().trim().split(':')[1]
                $('.filter-selectedFilterContainer').removeClass('d-none');
                $('.SortByList').append('<label id=order_list_shop>Sort By: </label><span class=ks-selected-items>'+ks_order+'</span><a class="remove_order_filter fa fa-times"><a/>')
            }
        })

        $(document).on('click','.remove_order_filter',function(ev){
            var temp = $('.sorting_active').attr('class').split(', ')[1].slice(0,-1).split(' ');
            var sort_val = temp[0] +'+'+temp[1]
            sort_val = sort_val.replace(/'/g,'')
            var cur_url = window.location.href;
            location.href = cur_url.replace(sort_val,'')
        });
        $(document).on('click','.remove_filter',function(ev){
            $(ev.currentTarget).attr('href','/shop?'+$('.ks_active').parent().find('a').attr('href').split('?').splice(1)[0]);
            $('.ks_active').parent().find('a').removeClass('ks_active active')
        });

        $(document).on('click','.remove_brand_filter',function(ev){
            if($('.price_filter_list').hasClass('d-none')){
                $("form.js_attributes").append('<input type="hidden" name="price_exp" value="False"/>');
            }
            var brand_key=$(ev.currentTarget).parent()[0].className
            _.each($('input[name="brnd"]:checked'), function(ev) {
                if (ev){
                    var a= "ks_var_filter_list " + $(ev).val();
                    if (a==brand_key){
                        $(ev).attr('checked',false);
                        var ks_order = $('.ks_sort_per_page').val();
                        if (ks_order !== undefined){
                            $("form.js_attributes").append('<input type="hidden" name="order" value="'+ks_order+'"/>').submit();
                        }
                        else{
                            $("form.js_attributes").submit();
                        }
                    }
                }
            })
        });

        $(document).on('click','.remove_price_filter',function(ev){
            var min=parseFloat($('#ks-price-filter').attr('data-slider-min'));
            var max=parseFloat($('#ks-price-filter').attr('data-slider-max'));
            if ($('#ks-price-filter').attr('data-slider-min')==undefined){
                min=0
            }
            if ($('#ks-price-filter').attr('data-slider-max')==undefined){
                max=0
            }
            var selected_min=parseFloat($('#ks-selected_input_min_hidden').val(min))
            var selected_max=parseFloat($('#ks-selected_input_max_hidden').val(max))
            var selected_min=parseFloat($('#ks-selected_input_min').val(min))
            var selected_max=parseFloat($('#ks-selected_input_max').val(max))
            var ks_order = $('.ks_sort_per_page').val();
            if (ks_order !== undefined){
                $("form.js_attributes").append('<input type="hidden" name="order" value="'+ks_order+'"/>').submit();
            }
            else{
                $("form.js_attributes").submit();
            }
        });

        $(document).on('click','.remove_variant_filter',function(ev){
            if($('.price_filter_list').hasClass('d-none')){
                $("form.js_attributes").append('<input type="hidden" name="price_exp" value="False"/>');
            }
            var variant_key=$(ev.currentTarget).parent()[0].className
            _.each($('.ks_attrib_active'), function(ev) {
                if (ev){
                    var a="ks_var_filter_list " + $(ev).find('input').val();
                    if (a==variant_key){
                        $(ev).find('input').attr('checked',false);
                        var ks_order = $('.ks_sort_per_page').val();
                        if (ks_order !== undefined){
                            $("form.js_attributes").append('<input type="hidden" name="order" value="'+ks_order+'"/>').submit();
                        }
                        else{
                            $("form.js_attributes").submit();
                        }
                    }
                }
            })
            if ($('select[name="attrib"]  option:selected').val()!=""){
                _.each($('.ks_select_attrib option:selected'), function(ev) {
                    if (ev){
                        var b="ks_var_filter_list " + $(ev).val();
                        if (b==variant_key){
                            $(ev).attr('selected',false);
                            var ks_order = $('.ks_sort_per_page').val();
                            if (ks_order !== undefined){
                                $("form.js_attributes").append('<input type="hidden" name="order" value="'+ks_order+'"/>').submit();
                            }
                            else{
                                $("form.js_attributes").submit();
                            }
                        }
                    }
                }
            )}
        });

        $("#ks-price-filter").slider({});

        $("#ks-price-filter").on("change",function(){
            if($(".is_ks_load_ajax").length === 0){
                var ks_price_val = $("#ks-price-filter").val();
                $("#ks-selected_input_min").val(ks_price_val[0]);
                $("#ks-selected_input_min_hidden").val(ks_price_val[0]);
                $("#ks-selected_input_max").val(ks_price_val[1]);
                $("#ks-selected_input_max_hidden").val(ks_price_val[1]);
                return false;
            }
        });

        $('.ks_price_input').on('input', function() {
            let minVal = parseFloat($('#ks-selected_input_min').val());
            let maxVal = parseFloat($('#ks-selected_input_max').val());
            $("#ks-selected_input_min_hidden").val(minVal);
            $("#ks-selected_input_max_hidden").val(maxVal);
            $('#ks-price-filter').slider('setValue', [minVal, maxVal])
        });

        $('.ks-price-filter-apply').on("click",function(e){
            var ks_price_val = $("#ks-price-filter").val();
            var ks_input_min_val = parseFloat($('#ks-selected_input_min_hidden').val())
            var ks_input_max_val = parseFloat($('#ks-selected_input_max_hidden').val())
            var ks_min_allow_val = parseFloat($("#ks-price-filter").attr('data-slider-min'))
            if ($('#ks-price-filter').attr('data-slider-min')==undefined){
                ks_min_allow_val=0.0
            }
            var ks_max_allow_val = parseFloat($("#ks-price-filter").attr('data-slider-max'))
            if ( ks_input_min_val <= ks_input_max_val && ks_input_min_val >= ks_min_allow_val && ks_input_min_val <= ks_max_allow_val &&
                 ks_input_max_val <= ks_max_allow_val && ks_input_max_val >= ks_min_allow_val){
                $("form.js_attributes").submit();
            }
            else{
                $('.ks_invalid_price_input').removeClass('d-none')
            }
            return false
        });

        if($('.o_rtl').length){
            var ks_rtl=true;
        }
//         this is slider of  hotel landing page
        $('.ks-hotel-gallery').owlCarousel({
            loop:true,
            margin:30,
            nav:true,
            rtl: ks_rtl,
            dots: false,
            navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
            autoplay: true,
            speed: 1000,
            responsive:{
                0:{
                    items:1,
                    dots: true,
                    nav: false,
                    margin: 0
                },
                600:{
                    items:3,
                    dots: true,
                    nav: false,
                    margin: 0
                },
                1000:{
                    items:4,
                    dots: true,
                    nav: false
                },
                1400: {
                    items: 4,
                }
            }
        });


//  this is for view mode toggling at shop page
        $('.list-view-group li').click(function(e){
            e.preventDefault();
            $(this).addClass('active');
            $('.ks-product-list').removeClass('col-lg-6')
            $('.ks-product-list').removeClass('col-lg-10')
            $('.ks-product-list').removeClass('col-lg-12')
            $('.ks-product-list').removeClass('col-lg-4')
            $('.ks-product-list').addClass('col-'+this.id)
            $(this).siblings().each(function(){
                $(this).removeClass('active') ;
            });
        });

        var pathname = window.location.pathname;
        var parts = pathname.split("/");
        var last_part = parts[parts.length-1];
        var page = parts[2];

        if($('.ks_alternate_slider').length){
            ks_p_id = $(".js_main_product").find(".product_template_id").val();
            ajax.jsonRpc("/ks_product_images", 'call', {"ks_p_id":ks_p_id}).then(function (data) {
                var i;
                var info;
                var name;
                var ks_navigation;
                var ks_repeat;
                var ks_speed;
                var ks_auto;
                var ks_rtl;
                for (i = 0; i < data.length; i++){
                    info =  data[i];
                    name = info['name'];
                    ks_repeat = info['ks_repeat'];
                    ks_speed = info['ks_speed'];
                    ks_auto = info['ks_auto'];
                    ks_rtl= info['rtl'];
                    ks_navigation = info['ks_navigation']
                    if(name == "Accessories"){
                        $(".accessories-prod-owl").owlCarousel({
                            items:2,
                            nav:ks_navigation,
                            autoplay:ks_auto,
                            margin:30,
                            rtl:ks_rtl,
                            loop:ks_repeat,
                            speed:ks_speed,
                            navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
                        });
                    }
                    if(name == "Alternate"){
                        $(".alternate-prod-owl").owlCarousel({
                        items:2,
                        autoplay:ks_auto,
                        nav:ks_navigation,
                        margin:30,
                        rtl:ks_rtl,
                        loop:ks_repeat,
                        speed:ks_speed,
                        navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
                        });
                    }
                }
            });
        };
    });
});
