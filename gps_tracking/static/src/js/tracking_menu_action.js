odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',

        events: {
            "click .btn-success": "_onClickIniciarViaje",
            "click .btn-warning": "_onClickPrueba",
        },

        willStart: async function () {
            const self = this;
            const result = await this._rpc({
                model: 'gps.device.trip',
                method: 'search_read',
                domain: [["state", "=", "ongoing"]],
                fields: ['check_in','device_id'],
                limit: 1,
            }).then(function (result) {
                self.current_trip = result.length ? result[0] : null;
            })
            return this._super.apply(this, arguments);
        },

        start: function () {  
            return this._super.apply(this, arguments);
        },

        renderElement: function () {
          this._super.apply(this, arguments);  
        },
        
        _onClickIniciarViaje: function () {
            this._startTrip();
        },

        _startTrip: function() {
            var self = this;
            var l = self.$el.find("#id_device").val();
            if(l != '') {
                if (/^\d{6}$/.test(l)) {
                    self.$el.find("#msg-text").text("");
                    self._rpc({
                        model: 'gps.device.trip',
                        method: '',
                        args:[l],
                    }).then(function (resultado) {

                    }).catch(function (error) {
                        console.error(error);
                    })
                } else {
                    self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
                    return;    
                }
            } else if (l == '') {
                self.$el.find("#msg-text").text("Ingrese el ID del dispositivo");
                return;
            }
        },

    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);  // Este es el tag que se llama en el XML
    return CustomCardMenu;
});
