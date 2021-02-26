odoo.define('website_recently_viewed_snippet', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    sAnimation.registry.snippet_recently_viewed_products = sAnimation.Class.extend({
       //select the element after which we are going append qweb
       selector: ".recently_viewed_products",
       //t-name of the snippet qweb
       template: 'ks_snippet_product_slider',
       //path of the qweb snippet file
        xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_product_slider.xml'],
       events: {
            'click .featured_btn': '_ksonFeaturedButtonsClick',
        },

        //sending all the products to qweb and than append it to the main element
        ks_handleFeaturedRecords:function(data){
          var ks_rtl=data['rtl']
          var $inner_temp = $(QWeb.render('ks_snippet_product_slider', {
                 "products": data,
         }));
          $inner_temp.find(".products-carousel").owlCarousel({
                  items:4,
                  autoplay:true,
                  margin:14,
                  speed:1300,
                  rtl: ks_rtl,
                  nav:true,
                  autoplayHoverPause: true,
                  navText:['<i class="fa fa fa-angle-left"></i>','<i class="fa fa fa-angle-right"></i>'],
                  responsiveClass: true,
                  responsive:{
                        0:{
                            items: 2,
                            dots: false,
                            margin:0,
                        },
                        960:{
                            items: 3,
                            dots: false
                        },
                        1200:{
                            items: 4,
                        }
                    },

               })
            $inner_temp.appendTo(this.$el.empty());

       },
       willStart:function(){
           this.$el.empty()
           return this._super();
       },
       start: function () {
            var self = this;
            self.ks_getFeaturedRecords();
            this.$el.empty()
//            $(".ks_featured_home_page").html("");
            return this._super();
        },
        ks_getFeaturedRecords:function(){
              var ks_self = this;
            //Fetching all the brands and rendering it with in snippet
            var tags = {}
            ajax.jsonRpc("/recently/viewed/products", 'call', {}).then(function (data) {
                    ks_self.ks_handleFeaturedRecords(data);
            });
        },
        //Handles the click of the tabs
        _ksonFeaturedButtonsClick:function(e){
            $('#product_btn_group button').removeClass('active')
            $(e.currentTarget).addClass('active')
//            $('#featured_row').addClass('tt_animation_trigger');
        },
    });
});