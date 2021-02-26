odoo.define('website_snippet_featured', function(require){
  "use strict";

    var sAnimation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var QWeb = core.qweb;
    sAnimation.registry.snippet_brands_home_page = sAnimation.Class.extend({
       //select the element after which we are going append qweb
       selector: ".ks_featured_home_page",
       //t-name of the snippet qweb
       template: 'snippet_featured',
       //path of the qweb snippet file
       xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_featured_snippet_inner.xml'],
       events: {
            'click .featured_btn': '_ksonFeaturedButtonsClick',
        },

        //sending all the products to qweb and than append it to the main element
        ks_handleFeaturedRecords:function(data){
          var $inner_temp = $(QWeb.render('snippet_featured', {
                 "products": data,
                 "new_arrivd_name": data[0].new_arrvd_tag_name,
                 "trendy_name": data[0].trendy_tag_name,
                 "ks_populae_tag_name": data[0].ks_populae_tag_name,
                 "ks_classics_tag_name": data[0].ks_classics_tag_name,
                 "ks_trendy_count": data[0].ks_trendy_count,
                 "new_arr_id_count": data[0].new_arr_id_count,
                 "ks_popular_count": data[0].ks_popular_count,
                 "ks_classics_count": data[0].ks_classics_count,
               }));
          $inner_temp.appendTo(this.$el);

       },
       start: function () {
            var self = this;
            self.ks_getFeaturedRecords();
            $(".ks_featured_home_page").html("");
            return this._super();
        },
        ks_getFeaturedRecords:function(){
              var ks_self = this;
            //Fetching all the brands and rendering it with in snippet
            var tags = {}
            ajax.jsonRpc("/product/featured", 'call', {}).then(function (data) {
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