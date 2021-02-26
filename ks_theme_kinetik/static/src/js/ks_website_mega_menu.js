odoo.define('ks_ecommerce_theme.website_mega_menu', function (require) {
    'use strict';
    var sAnimations = require('website.content.snippets.animation');

    sAnimations.registry.websiteMegaMenu = sAnimations.Class.extend({
        selector: '#top_menu li',
        read_events: {
            'mouseenter': '_onMouseEnter',
        },
        _onMouseEnter :function(ev){
          this.$el.find("#ks_categrory_slider_mm").owlCarousel({
                  items:1,
                  autoplay:true,
                  autoplayTimeout:1000,
                  margin:30,
                  autoplayHoverPause:true,
                  loop:true,
                  nav:true,
                  dots:false,
                  navText:['<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-left fa-stack-1x fa-inverse"></i></span>','<span class="fa-stack"><i class="fa fa-circle fa-stack-1x"></i><i class="fa fa-chevron-circle-right fa-stack-1x fa-inverse"></i></span>'],
               });
        },
     });

});