odoo.define('ks_theme_kinetik.product_grid', function(require) {
    "use strict";
      var session = require('web.session');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var Widget = require('web.Widget');
    var ks_widget = require('web_editor.widget');
    var animation = require('website.content.snippets.animation');
    var core = require('web.core');
    var website = require('website.utils');
    var options = require('web_editor.snippets.options');
    var ks_website_slider = require('ks_ecommerce_theme.product_multi_slider_base');

    var _t = core._t;
    var qweb = core.qweb;
    var ks_SnippetSelectionDialog = ks_widget.Dialog.extend({
        start: function() {
             var ks_self = this;
             ks_self.ks_setData(ks_self);
             ks_self._super();
        },
        ks_setData:function(modal){
                ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                        model: 'ks_product.grid',
                        method: 'search_read',
                        args: [],
                        kwargs: {
                            fields: ['name'],
                        }
                    }).then(function(data){
                     var select = $("<select></select>").attr("id", "ks_slider_selection").attr("name", "Selection slider");
                      $.each(data,function(index,json){
                       var ks_slider_id = "#"+(json.id)
                       if($(ks_slider_id).length === 0){
                         select.append($("<option></option>").attr("value", json.name).attr("id", json.id).text(json.name));
                       }
                     });
                     if(select.find("option").length){
                        $(modal.$el).append(select[0]);
                     }
                     else{
                        $(modal.$el).append(_t("No Grids For this page"));
                     }
                 });

        },
     });
    options.registry.product_grid_actions = options.Class.extend({
        on_prompt:function(ks_self){
                var dialog = new ks_SnippetSelectionDialog(ks_self, {
                    title: _t('Select Grid'),
                });
                dialog.open();
                dialog.on('save', this, function () {
                     var slider_id =  $('#ks_slider_selection').find(":selected").attr("id");
                     var ks_new_slider = new animation.registry.website_sale_product_grid(ks_self);
                     ks_new_slider.start(slider_id,ks_self);

                });
                dialog.on('cancel', this,function () {
                       this.$target.remove();
                });

        },
        onBuilt: function() {
                var ks_self = this;
                ks_self.on_prompt(ks_self)
                return this._super();
            },
       cleanForSave: function() {
            this.$target.empty();
        },
    });
});




