// odoo.define('gps_tracking.tracking_menu_action', function (require) {
//     "use strict";

//     const AbstractAction = require('web.AbstractAction');
//     const core = require('web.core');

//     const CustomCardMenu = AbstractAction.extend({
//         template: 'TrackingCardMenu',

//         events: {
//             "click .btn-success": "_onClickIniciarViaje",
//             "click .btn-warning": "_onClickPrueba",
//         },

//         willStart: async function () {
//             const self = this;
//             const result = await this._rpc({
//                 model: 'gps.device.trip',
//                 method: 'search_read',
//                 domain: [["state", "=", "ongoing"]],
//                 fields: ['check_in','device_id'],
//                 limit: 1,
//             }).then(function (result) {
//                 self.current_trip = result.length ? result[0] : null;
//             })
//             return this._super.apply(this, arguments);
//         },

//         start: function () {  
//             return this._super.apply(this, arguments);
//         },

//         renderElement: function () {
//           this._super.apply(this, arguments);  
//         },
        
//         _onClickIniciarViaje: function () {
//             this._startTrip();
//         },

//         _startTrip: function() {
//             var self = this;
//             var l = self.$el.find("#id_device").val();
//             if(l != '') {
//                 if (/^\d{6}$/.test(l)) {
//                     self.$el.find("#msg-text").text("");
//                     self._rpc({
//                         model: 'gps.device.trip',
//                         method: '',
//                         args:[l],
//                     }).then(function (resultado) {

//                     }).catch(function (error) {
//                         console.error(error);
//                     })
//                 } else {
//                     self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
//                     return;    
//                 }
//             } else if (l == '') {
//                 self.$el.find("#msg-text").text("Ingrese el ID del dispositivo");
//                 return;
//             }
//         },

//     });

//     core.action_registry.add('gps_tracking_tag', CustomCardMenu);  // Este es el tag que se llama en el XML
//     return CustomCardMenu;
// });
odoo.define('gps_tracking.tracking_menu_action', function (require) {
    "use strict";

    const AbstractAction = require('web.AbstractAction');
    const core = require('web.core');

    const CustomCardMenu = AbstractAction.extend({
        template: 'TrackingCardMenu',

        id_current_trip: null,
        hora_msg: null,
        estado_mensaje: null,
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

            // self.current_trip = result.length ? result[0] : null;
            await self._loadCurrentTrip();
            return AbstractAction.prototype.willStart.call(this);
        },

        start: function () {
            const self = this;
            self.id_current_trip = self.$el.find("#id_device").val();
            return AbstractAction.prototype.start.call(this);
        },

        _loadCurrentTrip: async function () {
          const result = await this._rpc({
              model: 'gps.device.trip',
              method: 'search_read',
              domain: [["state", "=", "ongoing"]],
              fields: ['check_in', 'start_time', 'device_id'],
              limit: 1,
          });
          this.current_trip = result.length ? result[0] : null;  
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
                var horaInicio = resultado.start_time;
                self.estado_mensaje = {
                    titulo: "Viaje iniciado",
                    texto: "El viaje ha iniciado correctamente. Fecha y Hora: " + horaInicio
                };
                self.renderElement();
                setTimeout(function () {
                    self.estado_mensaje = null;
                    self._reloadWidget();
                }, 5000)
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
                var horaInicio = resultado.start_time;
                var horaFin = resultado.end_time;
                var tiempoUsado = self._diffTime(horaInicio, horaFin);
                self.estado_mensaje = {
                    titulo: "Viaje finalizado",
                    texto: `Finalizó en ${tiempoUsado}`
                };
                self.renderElement();
                setTimeout(function () {
                    self.estado_mensaje = null;
                    self._reloadWidget();
                }, 5000)
                
            }).catch(function (error) {
                console.error(error);
                self.$el.find("#msg-text").text("Error al finalizar el viaje");
            });
        },

        _diffTime: function (horaStr1, horaStr2) {
            // Extraer horas, minutos y segundos
            const [h1, m1, s1] = horaStr1.split(":").map(Number);
            const [h2, m2, s2] = horaStr2.split(":").map(Number);

            // Usar una fecha ficticia común
            const d1 = new Date(0, 0, 0, h1, m1, s1);
            const d2 = new Date(0, 0, 0, h2, m2, s2);

            // Calcular la diferencia en milisegundos
            let diffMs = Math.abs(d1 - d2); // valor absoluto

            // Convertir a horas, minutos y segundos
            let horas = Math.floor(diffMs / (1000 * 60 * 60));
            diffMs %= (1000 * 60 * 60);
            let minutos = Math.floor(diffMs / (1000 * 60));
            diffMs %= (1000 * 60);
            let segundos = Math.floor(diffMs / 1000);

            return { horas, minutos, segundos };
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
        
    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);
    return CustomCardMenu;
});
