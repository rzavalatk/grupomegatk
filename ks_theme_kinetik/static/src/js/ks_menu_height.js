odoo.define('website.ks_theme_customization_menu_height', function (require) {
'use strict';

var sAnimations = require('website.content.snippets.animation');
var core = require('web.core');
var ks_websiteContentMenu=require('website.content.menu');
var _t = core._t;

var timeout;
sAnimations.registry.affixMenu.include({
                    _onWindowUpdate: function () {
                            if (this.$navbarCollapses.hasClass('show')) {
                                return;
                            }

                            var wOffset = $(window).scrollTop();
                            var hOffset = this.$target.scrollTop();
                            this.$headerClone.toggleClass('affixed', wOffset > (hOffset + 150));

                            // Reset opened menus
                            this.$dropdowns.removeClass('show');
                            this.$navbarCollapses.removeClass('show').attr('aria-expanded', false);
                        },

             })


    })