odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',

        events: {
            "click .btn-success": "_onClickPrueba",
            "click .btn-warning": "_onClickPrueba",
        },

        _onClickPrueba: function () {
            console.log("hola");
        },

        start: function () {
            
            return this._super.apply(this, arguments);
        },


    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);  // Este es el tag que se llama en el XML
    return CustomCardMenu;
});
