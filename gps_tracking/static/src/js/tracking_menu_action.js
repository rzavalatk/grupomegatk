odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',

        id_current_trip: null,

        events: {
            "click .btn-success": "_onClickIniciarViaje",
            "click .btn-warning": "_onClickFinalizarViaje",
        },

        // Método asincrónico corregido
        willStart: async function () {
            const self = this;

            const result = await this._rpc({
                model: 'gps.device.trip',
                method: 'search_read',
                domain: [["state", "=", "ongoing"]],
                fields: ['check_in', 'device_id'],
                limit: 1,
            });

            self.current_trip = result.length ? result[0] : null;

            return AbstractAction.prototype.willStart.call(this);
        },

        start: function () {
            const self = this;
            self.id_current_trip = self.$el.find("#id_device").val();
            return AbstractAction.prototype.start.call(this);
        },

        _onClickIniciarViaje: function () {
            this._startTrip();
        },

        _onClickFinalizarViaje: function () {
            console.log("Botón de prueba clickeado");
            console.log("Viaje actual:", this.current_trip);
            this._finishTrip();
        },

        _startTrip: function () {
            const self = this;
            self.id_current_trip = self.$el.find("#id_device").val();
            const deviceId = self.$el.find("#id_device").val();

            if (!deviceId) {
                self.$el.find("#msg-text").text("Ingrese el ID del dispositivo");
                return;
            }

            if (!/^\d{6}$/.test(deviceId)) {
                self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
                return;
            }

            self.$el.find("#msg-text").text("");

            self._rpc({
                model: 'gps.device.trip',
                method: 'start_trip', // <-- asegúrate de que este método exista
                args: [deviceId],
            }).then(function (resultado) {
                console.log("Resultado del inicio de viaje:", resultado);
                self._reloadWidget();
            }).catch(function (error) {
                console.error(error);
                self.$el.find("#msg-text").text("Error al iniciar el viaje");
            });
        },

        _finishTrip: function () {
            const self = this;
            var deviceId = self.$el.find("#id_device").val();
            self._rpc({
                model: 'gps.device.trip',
                method: 'finish_trip', // <-- asegúrate de que este método exista
                args: [self.current_trip.device_id],
            }).then(function (resultado) {
                console.log("Resultado del fin de viaje:", resultado);
                self._reloadWidget();
            }).catch(function (error) {
                console.error(error);
                self.$el.find("#msg-text").text("Error al finalizar el viaje");
            });
        },

        _reloadWidget: async function () {
            const self = this;
            const result = await this._rpc({
                model: 'gps.device.trip',
                method: 'search_read',
                domain: [["state", "=", "ongoing"]],
                fields: ['check_in','device_id'],
                limit: 1,
            });

            this.current_trip = result.length ? result[0] : null;

            this.$el.empty();         // Limpia el DOM actual
            this.renderElement();     // Re-renderiza el contenido desde el template
        },

        destroy: function () {
            this.$el.empty();
            $('#tracking_card_style').remove();
            this._super.apply(this, arguments);
        },

    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);
    return CustomCardMenu;
});