odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    core = require('web.core');
    var AbstractAction = require('web.AbstractAction');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',

        start: function () {
            console.log("funciona");
            
            return this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);
    return CustomCardMenu;
});