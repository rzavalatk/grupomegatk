odoo.define('control_visitas.visitas_menu_action', function (require) {
"use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var CustomDashboard = AbstractAction.extend({
        template: 'VisitasMenuDashboard',

        value_filtro: null,
        
        events: {
            'change #filter_region': '_onChangeFilter',
        },

        _onChangeFilter: function (ev) {
            ev.preventDefault();
            console.log("Desde onChangeFilter " + this.value_filtro);
            this.value_filtro = ev.target.value;
            console.log("Desde onChangeFilter " + this.value_filtro);
            this._updateView();
        },

        _updateView: function () {
            var self = this;
            var reg = "";

            if(self.value_filtro == "reg_tgu") {
                reg = "_tgu";
                self._updateUI(reg);   
            } else if(self.value_filtro == "reg_sps") {
                reg = "_sps";
                self._updateUI(reg);
            }
            
        },

        _updateUI: function (reg) {
            var self = this;
        
            // Definir funciones con nombre para manejar los eventos click
            const manejarClickAdminState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_administracion',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#admin_value").text(resultado[`admin${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickMegatkState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_tienda_megatk',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#megatk_value").text(resultado[`megatk${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickMeditekState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_tienda_meditek',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#meditek_value").text(resultado[`meditek${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickLenkaState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_lenka',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#lenka_value").text(resultado[`lenka${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickClinicaState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_clinica',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#clinica_value").text(resultado[`clinica${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickGerenciaState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_gerencia',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#gerencia_value").text(resultado[`gerencia${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickSoporteState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_soporte',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#soporte_value").text(resultado[`soporte${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            const manejarClickOtrosState = () => {
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_otros',
                    args: [],
                }).then(function (resultado) {
                    self.$el.find("#otros_value").text(resultado[`otros${reg}`]);
                }).catch(function (error) {
                    console.error(error);
                });
            }
        
            // Obtener los datos iniciales
            ajax.rpc(`/control_visitas${reg}`).then(function (result) {
                
                // Eliminar eventos anteriores para evitar duplicación
                self.$el.off('click', '#admin_state');
                self.$el.off('click', '#megatk_state');
                self.$el.off('click', '#meditek_state');
                self.$el.off('click', '#lenka_state');
                self.$el.off('click', '#clinica_state');
                self.$el.off('click', '#gerencia_state');
                self.$el.off('click', '#soporte_state');
                self.$el.off('click', '#otros_state');
        
                // Actualizar los valores en la interfaz
                self.$el.find("#admin_value").text(result.admin);
                self.$el.find("#meditek_value").text(result.meditek);
                self.$el.find("#lenka_value").text(result.lenka);
                self.$el.find("#clinica_value").text(result.clinica);
                self.$el.find("#megatk_value").text(result.megatk);
                self.$el.find("#gerencia_value").text(result.gerencia);
                self.$el.find("#soporte_value").text(result.soporte);
                self.$el.find("#otros_value").text(result.otros);
        
                // Registrar los eventos click con las funciones con nombre
                self.$el.on('click', '#admin_state', manejarClickAdminState);
                self.$el.on('click', '#megatk_state', manejarClickMegatkState);
                self.$el.on('click', '#meditek_state', manejarClickMeditekState);
                self.$el.on('click', '#lenka_state', manejarClickLenkaState);
                self.$el.on('click', '#clinica_state', manejarClickClinicaState);
                self.$el.on('click', '#gerencia_state', manejarClickGerenciaState);
                self.$el.on('click', '#soporte_state', manejarClickSoporteState);
                self.$el.on('click', '#otros_state', manejarClickOtrosState);
        
                // Manejar el cambio en el filtro
                self.$el.find("#filter_selection").off('change').on('change', function (e) {
                    var target = $(e.target);
                    var value = target.val();
                    var val_filter = value + reg;
        
                    if (val_filter == `this_day${reg}`) {
                        ajax.rpc(`/control_visitas_dia${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                        });
                    } else if (val_filter == `this_week${reg}`) {
                        ajax.rpc(`/control_visitas_semana${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                        });
                    } else if (val_filter == `this_month${reg}`) {
                        ajax.rpc(`/control_visitas_mes${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                        });
                    } else if (val_filter == `this_year${reg}`) {
                        ajax.rpc(`/control_visitas_anio${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                        });
                    }
                });
            });
        },

        start: function () {
            var self = this;

            ajax.rpc('/control_visitas_user_reg').then(function (result) {

                if(result.user_reg == "TGU") {
                    self.value_filtro = "reg_tgu";
                } else if(result.user_reg == "SPS") {
                    self.value_filtro = "reg_sps";
                }

                self._updateView();
                console.log("Desde start " + self.value_filtro);
                
                return self._super.apply(self, arguments);
            })
        },
    })
    core.action_registry.add('control_visitas_tag', CustomDashboard);
    return CustomDashboard;
});
