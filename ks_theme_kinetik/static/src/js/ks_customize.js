odoo.define('ks_theme_customizeMenu', function (require) {
    'use strict'
    var ks_CustomizeMenu = require('website.customizeMenu');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var ColorpickerDialog = require('web.colorpicker');
    var qweb = core.qweb;


    var ThemeCustomize = ks_CustomizeMenu.include({
             _onCustomizeOptionClick: function (ev) {
                $('.o_theme_customize_modal').hide();
                this._super(ev);
            },
          _loadCustomizeOptions: function () {
             if (this.__customizeOptionsLoaded) {
                    return $.when();
                }
                this.__customizeOptionsLoaded = true;

                var $menu = this.$el.children('.dropdown-menu');
                return this._rpc({
                    route: '/website/get_switchable_related_views',
                    params: {
                        key: this.viewName,
                    },
                }).then(function (result) {
                    var currentGroup = '';
                    _.each(result, function (item) {
                        if (currentGroup !== item.inherit_id[1]) {
                            currentGroup = item.inherit_id[1];
                            $menu.append('<li class="dropdown-header">' + currentGroup + '</li>');
                        }
                        var $a = $('<a/>', {href: '#', class: 'dropdown-item', 'data-view-id': item.id, role: 'menuitem'})
                                    .append(qweb.render('web_editor.components.switch', {id: 'switch-' + item.id, label: item.name}));
                        $a.find('input').prop('checked', !!item.active);
                        if ((item.key.indexOf('ks_theme_kinetik.custom_header_layout')!= -1) ||
                            (item.key.indexOf('ks_theme_kinetik.ks_button_style_layout')!= -1) ||
                            (item.key.indexOf('ks_theme_kinetik.custom_font_layout')!= -1) ||
                            (item.key.indexOf('ks_theme_kinetik.custom_snippet_width')!= -1) ||
                            (item.key.indexOf('ks_theme_kinetik.custom_footer_layout')!= -1)){
                                       $a.addClass("d-none");
                                       $menu.append($a);
                                       $(".header_layout_selection").append($a);
                        }
                        else{
                            $menu.append($a);
                            $(".header_layout_selection").append($a)
                        }

                    });
                });
                }

          });


    });