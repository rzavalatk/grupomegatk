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
            // const self = this;
            // self.id_current_trip = self.$el.find("#id_device").val();
            // const deviceId = self.$el.find("#id_device").val();

            // if (!deviceId) {
            //     self.$el.find("#msg-text").text("Ingrese el ID del dispositivo");
            //     return;
            // }

            // if (!/^\d{6}$/.test(deviceId)) {
            //     self.$el.find("#msg-text").text("El ID del dispositivo no es válido");
            //     return;
            // }

            // self.$el.find("#msg-text").text("");

            // self._rpc({
            //     model: 'gps.device.trip',
            //     method: 'start_trip',
            //     args: [deviceId],
            //     kwargs: { employee_id: await self._getCurrentEmployee() },
            // }).then(function (resultado) {
            //     console.log("Resultado del inicio de viaje:", resultado);
            //     self._reloadWidget();
            // }).catch(function (error) {
            //     console.error(error);
            //     self.$el.find("#msg-text").text("Error al iniciar el viaje");
            // });
            const deviceId = $("#id_device").val();

            if (!deviceId) {
                $('#msg-text').text("Ingrese el ID del dispositvo");
                return;
            } else {
                console.log(deviceId);
                
                await self._rpc({
                    model: 'gps.device.trip',
                    method: 'check_id',
                    args: [deviceId],
                }).then(async function (result) {
                    if(result) {
                        if(!/^\d{6}$/.test(deviceId)) {
                            $('#msg-text').text("El ID del dispositivo no es válido");
                            return;
                        } else {
                            $('#msg-text').text("");    
                            await self._rpc({
                                model: 'gps.device.trip',
                                method: 'start_trip',
                                args: [deviceId],
                            }).then(function (result) {
                                console.log("Resultado del inicio de viaje:", result);
                                self._reloadWidget();
                                
                            }).catch(function (error) {
                                console.error(error);
                                $("#msg-text").text("Error al cargar el viaje");
                            });
                        }
                    } else {
                        $('#msg-text').text("El ID del dispositivo no existe");
                        return;
                    }
                })
            }
        },

        _finishTrip: async function () {
            const self = this;
            console.log("self.getCurrentEmployee", await self._getCurrentEmployee());
            
            self._rpc({
                model: 'gps.device.trip',
                method: 'finish_trip',
                args: [self.current_trip.device_id, await self._getCurrentEmployee()],
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

            console.log("Empleado current: ", employee.length ? employee[0] : false);
            
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