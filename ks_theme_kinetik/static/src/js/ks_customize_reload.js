odoo.define('ks_theme_customization_reload', function (require) {
    'use strict'
    var ks_websitecustmizeMenu = require('website.customizeMenu');

    var ThemeCustomizeReload = ks_websitecustmizeMenu.include({

    xmlDependencies: ['/web_editor/static/src/xml/editor.xml'],
    events: {
        'show.bs.dropdown': '_onDropdownShow',
        'click .dropdown-item[data-view-id]': '_onCustomizeOptionClick',
    },
    _doCustomize: function (viewID) {
        return this._rpc({
            model: 'ir.ui.view',
            method: 'toggle',
            args: [[viewID]],
        }).then(function () {
            if($(".ks_customize_dropdown_items").length){
                  return $.Deferred();

            }else{
                  window.location.reload();
                 return $.Deferred();
            }
        });
    },


     _onCustomizeOptionClick: function (ev) {
        ev.preventDefault();
//        $(ev.currentTarget).find('label').addClass('ks_header_active');
        var viewID = parseInt($(ev.currentTarget).data('view-id'), 10);
        this._doCustomize(viewID);
    },


})
        $(document).on('click','#save_footer',function(){
                   location.reload();
                  })

    })