odoo.define('website_new_snippet', function(require){
  "use strict";
   var options = require('web_editor.snippets.options');
   var WebsiteNewMenu = require('website.newMenu');
   var ks_snippet_editor = require('web_editor.snippet.editor');
   var ks_core = require("web.core");
   var widget = require('web_editor.widget');
   var ajax = require('web.ajax');
   var _t = ks_core._t;
   var rpc = require('web.rpc');
   var QWeb = ks_core.qweb;

   ks_snippet_editor.Class.include({
         start: function () {
            //TODO check why odoo snippet editor can not handling iframes
//            $(".ks_iframe iframe").replaceWith("<div groups='website.group_website_publisher' style='height: 100px; font-size:24px;' class='w-100 text-center font-weight-bold'><div>Google Map Or Other Iframe</div><div class='font-weight-normal font-italic'> If you are editing Please delete me and again drop your snippet here </div></div>");
            return this._super.apply(this, arguments);

        },
        _computeSnippetTemplates: function(html) {
            var $html = $('<div/>').append(html);
            var new_snippets;
            var ks_self = this;
            var sup;
            var _sup = this._super
             var def =  rpc.query({
                 model: 'theme.ks_new_snippet',
                 method: 'search_read',
             }).then(function(ks, sup, new_snippets){
                      for (var i in new_snippets) {
                          var snippet = '<div name=' + JSON.stringify(new_snippets[i].display_name) +' data-oe-type=snippet'+" "+'data-oe-thumbnail="/web/image/theme.ks_new_snippet/'+new_snippets[i].id+'/ks_snippet_thumbnail"'+'>' +
                             '<section class="snippet-snippet ks_iframe website_snippet_' + new_snippets[i].id+'"'+'>' + new_snippets[i].ks_snippet_body +'</section>' +
                             '</div>';
                         $html.find('#custom_snippets .o_panel_body').append(snippet);
                     }
                      _sup.call(ks_self, $html.html());
             }.bind(ks_self, _sup,new_snippets));
        },
    });


   var NewSnippetDialog = widget.Dialog.extend({
        start: function() {
             var ks_self = this;
             var def,data;
              ks_self.def = ajax.loadJS("/web/static/lib/ace/ace.js");
              $.when(ks_self.def).then(function() {
                    ajax.loadJS("/web/static/lib/ace/theme-monokai.js");
                    ajax.loadJS("/web/static/lib/ace/mode-xml.js");
                    ajax.loadJS("/web/static/lib/ace/mode-scss.js");
               }).then(function(){
                    ks_self.ks_Editor = window.ace.edit(ks_self.$el.find(".ks-editor")[0]);
                    ks_self.ks_Editor.setTheme("ace/theme/monokai");
                    ks_self.ks_Editor.getSession().setMode("ace/mode/xml");

                    ks_self.ks_css_editor = window.ace.edit(ks_self.$el.find(".ks-css-editor")[0]);
                    ks_self.ks_css_editor.setTheme("ace/theme/monokai");
                    ks_self.ks_css_editor.getSession().setMode("ace/mode/scss");
                });
             ks_self._super();
        },
        save:function(){
            var ks_self = this;
            var ks_snippet_html = ks_self.ks_Editor.getValue();
            var ks_snippet_css = ks_self.ks_css_editor.getValue();
            var ks_wrapped_html = $(ks_snippet_html).wrap("<section class='oe_snippet_body'></section>");
//            var ks_html = ks_emty_var.append(ks_snippet_html);
            var ks_snippet_name = ks_self.$el.find(".ks_snippet_name").val();
            ks_self._super();
            ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                model: 'theme.ks_new_snippet',
                method: 'create',
                args: [{
                        'name': ks_snippet_name,
                        'ks_snippet_body': ks_wrapped_html.html(),
                        'ks_snippet_css': ks_snippet_css,
                        }],
                kwargs: {}
            }).then(function(){
                location.reload();
            });
        }
    });


     ks_snippet_editor.Class.include({
         xmlDependencies: ['/ks_theme_kinetik/static/src/xml/ks_new_snippet.xml'],
        _makeSnippetDraggable: function ($snippets) {
            var ks_self = this;
            ks_self._super($snippets);

            ks_self.on("snippet_dropped",this,function(ev){
                if(ev.data.$target.hasClass("ks_snippet_new")){
                     ks_core.bus.trigger_up("ks_new_snippet_dropped");

                }
           });
        ks_core.bus.on("ks_new_snippet_dropped",this,function(ev){
             var ks_self = this;
             var dialog = new NewSnippetDialog(ks_self, {
                    title: _t('Add HTML'),
                    $content: QWeb.render('ks_theme_kinetik.ks_new_snippet')
                });
              dialog.open()
         });
        },

    });
});
