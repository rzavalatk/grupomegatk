odoo.define('website_snippet_trendy_style_2', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    sAnimation.registry.ks_trendy_style_static = sAnimation.Class.extend({
       selector: ".ks_trending_static",
       template: 'ks_trendy',
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_trendy_style_qweb.xml'],
        ks_handleFeaturedRecords:function(data){
          var $inner_temp = $(QWeb.render('ks_trendy', {
                 "ks_prods_info": data,
               }));
          $inner_temp.appendTo(this.$el);

       },
       start: function () {
            var self = this;
            self.ks_getFeaturedRecords();
            $(".ks_trending_static").html("");
            return this._super();
        },
        ks_getFeaturedRecords:function(){
              var ks_self = this;
            var tags = {}
            ajax.jsonRpc("/trendy_style", 'call', {}).then(function (data) {
                    ks_self.ks_handleFeaturedRecords(data);
            });
        },

    });
});