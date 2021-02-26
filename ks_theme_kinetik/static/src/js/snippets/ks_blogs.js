odoo.define('website_dynamic_blogs', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    sAnimation.registry.snippet_blogs_home_page = sAnimation.Class.extend({
       selector: ".ks_dynamic_blog",
       template: 'ks_dynamic_blog_new',
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_dynamic_blogs.xml'],

        ks_handleBlogsRecords:function(data){
          var $inner_temp = $(QWeb.render('ks_dynamic_blog_new', {
                 "ks_blog_info": data,
               }));
          $inner_temp.appendTo(this.$el);

       },
       start: function () {
            var self = this;
            self.ks_getFeaturedRecords();
            $(".ks_dynamic_blog").html("");
            return this._super();
        },
        ks_getFeaturedRecords:function(){
              var ks_self = this;
            var tags = {}
            ajax.jsonRpc("/ks_blogs", 'call', {}).then(function (data) {
                    ks_self.ks_handleBlogsRecords(data);
            });
        },

    });
});