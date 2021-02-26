odoo.define('website_snippet_brands', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
     var Dialog = require('web.Dialog');
     var core = require('web.core');
    var QWeb = core.qweb;


    sAnimation.registry.snippet_featured_home_page = sAnimation.Class.extend({
        selector: ".ks_brands_home_page",
        template: 'ks_snippet_product_brand',
        xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_brand.xml'],
        //Get all the records iterate through all records

        handleRecords:function(data){
            var aos_delay  = 0;
             var $inner_temp = $(QWeb.render('ks_snippet_product_brand', {
                  "record": data,
                  "aos_delay" : aos_delay
               }));
          $inner_temp.appendTo(this.$el);

        },

        start: function () {
            var self = this;
            self.getRecords();
            $(".ks_brands_home_page").html("");
            return this._super();

        },
         getRecords: function() {
            var ks_self = this;
            //Fetching all the brands and rendering it with in snippet
            ajax.jsonRpc("/product_brands", 'call', {}).then(function (data) {
                    ks_self.handleRecords(data);
            });
        },
    });

});


