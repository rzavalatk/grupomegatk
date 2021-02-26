odoo.define('website_snippet_main_slider', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    sAnimation.registry.snippet_main_slider = sAnimation.Class.extend({
       //select the element after which we are going append qweb/shop/product/
       selector: ".mainHomeSlider",
       //t-name of the snippet qweb
       template: 'ks_main_slider',
       //path of the qweb snippet file
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_main_slider.xml'],


        //sending all the products to qweb and than append it to the main element
        ks_handleFeaturedRecords:function(data){
          var $inner_temp = $(QWeb.render('ks_main_slider', {
                        "slides": data[0],
                     }));
          $inner_temp.appendTo(this.$el);
          $("#owl-main-carousel").owlCarousel({
                  navigation : true, // Show next and prev buttons
                  slideSpeed : 300,
                  rtl: data[1],
                  paginationSpeed : 400,
                  animateIn: 'slideInRight',
                  animateOut: 'slideOutLeft',
                  items : 1,
                  autoHeight: false,
                  responsiveClass: true,
                  itemsDesktop : false,
                  itemsDesktopSmall : false,
                  itemsTablet: false,
                  itemsMobile : false
             });

       },
       start: function () {
            var self = this;
            self.ks_getRecords();
            $(".mainCarouselIndicator").html("");
            return this._super();
        },
        ks_getRecords:function(){
             var ks_self = this;
             ajax.jsonRpc("/get/main/slider/data", 'call', {}).then(function (data) {
                    ks_self.ks_handleFeaturedRecords(data);
             });
        },
    });
});