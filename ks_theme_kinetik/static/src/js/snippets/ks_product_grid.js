odoo.define('ks_theme_kinetik.ks_product_grid', function(require){
  "use strict";

    var session = require('web.session');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var animation = require('website.content.snippets.animation');
    var core = require('web.core');
    var website = require('website.utils');

    var _t = core._t;
    var qweb = core.qweb;

    animation.registry.website_sale_product_grid = animation.Class.extend({
        selector: ".snippet_product_grid",
        widget: null,
        template: 'ks_snippet_product_grid',
        xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_product_grid_snippet.xml'],

        ks_handleRecords:function(data,$target){
          var $inner_temp = $(qweb.render('ks_snippet_product_grid', {
                 "products": data,
               }));
               if($target){
                   $inner_temp.appendTo($target.empty());
               }
        },
        start: function(slider_id,ks_self_recived) {
            var ks_self = this;

            if(ks_self_recived !== undefined){
                ks_self = ks_self_recived;
                ks_self.$target.attr('data-id', slider_id);
                this.$el = ks_self_recived.$el;
                this.$target = ks_self_recived.$target;
                this.data = ks_self_recived.data;
                this.overlay = ks_self_recived.overlay;
            }
            var $target = ks_self.$target;
            var id = ks_self.$target.attr('data-id');

            if (!id) {
                return;
            }

            ajax.jsonRpc("/product/data", 'call', {"snippet_name":"grid","id":id}).then(function (data) {
                    this.ks_handleRecords(data,$target);
            }.bind(this));

        },
        stop: function() {
            this.widget.destroy();
        }
    });
});