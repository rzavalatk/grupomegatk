// // odoo.define('gps_tracking.tracking_menu_action', function (require) {
// //     "use strict";

// //     const AbstractAction = require('web.AbstractAction');
// //     const core = require('web.core');
// //     let activeTrackingWidget = false;

// //     const CustomCardMenu = AbstractAction.extend({
// //         template: 'TrackingCardMenu',

// //         id_current_trip: null,

// //         events: {
// //             "click .btn-success": "_onClickIniciarViaje",
// //             "click .btn-warning": "_onClickFinalizarViaje",
// //         },

// //         // Método asincrónico corregido
// //         willStart: async function () {
// //             const self = this;

// //             const result = await this._rpc({
// //                 model: 'gps.device.trip',
// //                 method: 'search_read',
// //                 domain: [["state", "=", "ongoing"]],
// //                 fields: ['check_in', 'device_id'],
// //                 limit: 1,
// //             });

// //             self.current_trip = result.length ? result[0] : null;

// //             return AbstractAction.prototype.willStart.call(this);
// //         },

// //         start: function () {
// //             const self = this;
// //             // return AbstractAction.prototype.start.call(this);
// //             this._super.apply(this, arguments);
// //             this.actionManager && this.actionManager.doAction && this.actionManager.on('will_clear_action', this, this._onWillClearAction); // <&&
// //         },

// //         _onClickIniciarViaje: function () {
// //             this._startTrip();
// //         },

// //         _onClickFinalizarViaje: function () {
// //             console.log("Botón de prueba clickeado");
// //             console.log("Viaje actual:", this.current_trip);
// //             this._finishTrip();
// //         },

// //         _startTrip: function () {
// //             const self = this;
// //             self.id_current_trip = self.$el.find("#id_device").val();
// //             const deviceId = self.$el.find("#id_device").val();

// //             if (!deviceId) {
// //                 self.$el.find("#msg-text").text("Ingrese el ID del dispositivo");
// //                 return;
// //             }

// //             if (!/^\d{6}$/.test(deviceId)) {
// //                 self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
// //                 return;
// //             }

// //             self.$el.find("#msg-text").text("");

// //             self._rpc({
// //                 model: 'gps.device.trip',
// //                 method: 'start_trip', // <-- asegúrate de que este método exista
// //                 args: [deviceId],
// //             }).then(function (resultado) {
// //                 console.log("Resultado del inicio de viaje:", resultado);
// //                 self._reloadWidget();
// //             }).catch(function (error) {
// //                 console.error(error);
// //                 self.$el.find("#msg-text").text("Error al iniciar el viaje");
// //             });
// //         },

// //         _finishTrip: function () {
// //             const self = this;
// //             var deviceId = self.$el.find("#id_device").val();
// //             self._rpc({
// //                 model: 'gps.device.trip',
// //                 method: 'finish_trip', // <-- asegúrate de que este método exista
// //                 args: [self.current_trip.device_id],
// //             }).then(function (resultado) {
// //                 console.log("Resultado del fin de viaje:", resultado);
// //                 self._reloadWidget();
// //             }).catch(function (error) {
// //                 console.error(error);
// //                 self.$el.find("#msg-text").text("Error al finalizar el viaje");
// //             });
// //         },

// //         _reloadWidget: async function () {
// //             const self = this;
// //             const result = await this._rpc({
// //                 model: 'gps.device.trip',
// //                 method: 'search_read',
// //                 domain: [["state", "=", "ongoing"]],
// //                 fields: ['check_in','device_id'],
// //                 limit: 1,
// //             });

// //             this.current_trip = result.length ? result[0] : null;

// //             this.$el.empty();         // Limpia el DOM actual
// //             this.renderElement();     // Re-renderiza el contenido desde el template
// //         },


// //         _onWillClearAction: function () {
// //             console.log("Se disparó will_clear_action, destrucción forzada del widget");
// //             this.destroy();
// //             this.$el.remove(); // Remueve el DOM manualmente si aún queda algo
// //         },

// //         destroy: function () {
// //             console.log("Destruyendo el widget");
// //             this._super.apply(this, arguments);
// //         },

// //     });

// //     core.action_registry.add('gps_tracking_tag', CustomCardMenu);
// //     return CustomCardMenu;
// // });
// odoo.define('gps_tracking.tracking_menu_action', function (require) {
//     "use strict";

//     const AbstractAction = require('web.AbstractAction');
//     const core = require('web.core');

//     const CustomCardMenu = AbstractAction.extend({
//         template: 'TrackingCardMenu',
//         id_current_trip: null,
//         events: {
//             "click .btn-success": "_onClickIniciarViaje",
//             "click .btn-warning": "_onClickFinalizarViaje",
//         },

//         willStart: async function () {
//             const self = this;
//             const result = await this._rpc({
//                 model: 'gps.device.trip',
//                 method: 'search_read',
//                 domain: [["state", "=", "ongoing"]],
//                 fields: ['check_in', 'device_id'],
//                 limit: 1,
//             });
//             self.current_trip = result.length ? result[0] : null;
//             return AbstractAction.prototype.willStart.call(this);
//         },

//         start: function () {
//             this._super.apply(this, arguments);
//             // Asegurarse de que el listener se añada al ActionManager existente
//             if (this.actionManager) {
//                 this.actionManager.on('will_clear_action', this, this._onWillClearAction);
//             }
//             return Promise.resolve(); // start debe retornar una promesa
//         },

//         _onClickIniciarViaje: function () {
//             this._startTrip();
//         },

//         _onClickFinalizarViaje: function () {
//             this._finishTrip();
//         },

//         _startTrip: function () {
//             const self = this;
//             self.id_current_trip = self.$el.find("#id_device").val();
//             const deviceId = self.$el.find("#id_device").val();

//             if (!deviceId) {
//                 self.$el.find("#msg-text").text("Ingrese el ID del dispositivo");
//                 return;
//             }

//             if (!/^\d{6}$/.test(deviceId)) {
//                 self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
//                 return;
//             }

//             self.$el.find("#msg-text").text("");

//             self._rpc({
//                 model: 'gps.device.trip',
//                 method: 'start_trip',
//                 args: [deviceId],
//             }).then(function (resultado) {
//                 console.log("Resultado del inicio de viaje:", resultado);
//                 self._reloadWidget();
//             }).catch(function (error) {
//                 console.error(error);
//                 self.$el.find("#msg-text").text("Error al iniciar el viaje");
//             });
//         },

//         _finishTrip: function () {
//             const self = this;
//             self._rpc({
//                 model: 'gps.device.trip',
//                 method: 'finish_trip',
//                 args: [self.current_trip.device_id],
//             }).then(function (resultado) {
//                 console.log("Resultado del fin de viaje:", resultado);
//                 self._reloadWidget();
//             }).catch(function (error) {
//                 console.error(error);
//                 self.$el.find("#msg-text").text("Error al finalizar el viaje");
//             });
//         },

//         _reloadWidget: async function () {
//             const self = this;
//             const result = await this._rpc({
//                 model: 'gps.device.trip',
//                 method: 'search_read',
//                 domain: [["state", "=", "ongoing"]],
//                 fields: ['check_in','device_id'],
//                 limit: 1,
//             });

//             this.current_trip = result.length ? result[0] : null;

//             this.$el.empty();
//             this.renderElement();
//         },

//         _onWillClearAction: function () {
//             console.log("Se disparó will_clear_action - Destruyendo widget");
//             this.destroy();
//             // Intenta remover el elemento del DOM de forma más directa
//             if (this.$el && this.$el.length) {
//                 this.$el.detach(); // detach también elimina los eventos asociados
//                 console.log("Elemento del widget removido del DOM");
//             } else {
//                 console.log("El elemento del widget no existe o ya fue removido");
//             }
//         },

//         destroy: function () {
//             console.log("Método destroy llamado");
//             // Desasociar el listener para evitar ejecuciones innecesarias
//             if (this.actionManager) {
//                 this.actionManager.off('will_clear_action', this, this._onWillClearAction);
//             }
//             this._super.apply(this, arguments);
//             console.log("Widget destruido");
//         },
//     });

//     core.action_registry.add('gps_tracking_tag', CustomCardMenu);
//     return CustomCardMenu;
// });
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

        willStart: async function () {
            const self = this;
            const currentEmployee = await self._getCurrentEmployee();
            let domain = [["state", "=", "ongoing"]];
            if (currentEmployee) {
                domain.push(['id_employee', '=', currentEmployee]);
            }
            const result = await this._rpc({
                model: 'gps.device.trip',
                method: 'search_read',
                domain: domain,
                fields: ['check_in', 'device_id'],
                limit: 1,
            });
            self.current_trip = result.length ? result[0] : null;
            return AbstractAction.prototype.willStart.call(this);
        },

        start: function () {
            this._super.apply(this, arguments);
            if (this.actionManager) {
                this.actionManager.on('will_clear_action', this, this._onWillClearAction);
            }
            return Promise.resolve();
        },

        _onClickIniciarViaje: function () {
            this._startTrip();
        },

        _onClickFinalizarViaje: function () {
            this._finishTrip();
        },

        _startTrip: async function () {
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
                method: 'start_trip',
                args: [deviceId],
                kwargs: { employee_id: await self._getCurrentEmployee() },
            }).then(function (resultado) {
                console.log("Resultado del inicio de viaje:", resultado);
                self._reloadWidget();
            }).catch(function (error) {
                console.error(error);
                self.$el.find("#msg-text").text("Error al iniciar el viaje");
            });
        },

        _finishTrip: async  function () {
            const self = this;
            console.log("self.getCurrentEmployee", await self._getCurrentEmployee());
            
            self._rpc({
                model: 'gps.device.trip',
                method: 'finish_trip',
                args: [self.current_trip.device_id, self._getCurrentEmployee()],
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
            const currentEmployee = await self._getCurrentEmployee();
            let domain = [["state", "=", "ongoing"]];
            if (currentEmployee) {
                domain.push(['id_employee', '=', currentEmployee]);
            }
            const result = await this._rpc({
                model: 'gps.device.trip',
                method: 'search_read',
                domain: domain,
                fields: ['check_in', 'device_id'],
                limit: 1,
            });
            
            this.current_trip = result.length ? result[0] : null;

            this.$el.empty();
            this.renderElement();
        },

        _getCurrentEmployee: async function () {
            const employee = await this._rpc({
                model: 'hr.employee',
                method: 'search_read',
                domain: [['user_id', '=', this.getSession().uid]],
                fields: ['id'],
                limit: 1,
            });
            console.log("Empleado actual:", employee[0].id);
            console.log("Empleado current: ", employee.length ? employee[0].id : false);
            
            return employee.length ? employee[0].id : false;
        },

        _onWillClearAction: function () {
            console.log("Se disparó will_clear_action - Destruyendo widget");
            this._destroyWidget();
        },

        on_detach_callback: function () {
            console.log("Se llamó on_detach_callback - Destruyendo widget");
            this._destroyWidget();
        },

        _destroyWidget: function () {
            console.log("Destruyendo el widget");
            if (this.actionManager) {
                this.actionManager.off('will_clear_action', this, this._onWillClearAction);
            }
            this.destroy();
            if (this.$el && this.$el.length) {
                this.$el.detach();
                console.log("Elemento del widget removido del DOM");
            } else {
                console.log("El elemento del widget no existe o ya fue removido");
            }
            console.log("Widget destruido");
        },

        destroy: function () {
            console.log("Método destroy llamado (desde destroyWidget)");
            this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('gps_tracking_tag', CustomCardMenu);
    return CustomCardMenu;
});