odoo.define('control_visitas.visitas_menu_action', function (require) {
    "use strict";
    
        var AbstractAction = require('web.AbstractAction');
        var core = require('web.core');
        var rpc = require('web.rpc');
        var ajax = require('web.ajax');
        var CustomDashboard = AbstractAction.extend({
            template: 'VisitasMenuDashboard',
    
            value_filtro: null,
    
            filtro_dias: null,
            
            events: {
                'change #filter_region': '_onChangeFilter',
                'click .btn-admin': '_onClickDeleteRecord',
                'click .btn-megatk': '_onClickDeleteRecord',
                'click .btn-meditek': '_onClickDeleteRecord',
                'click .btn-lenka': '_onClickDeleteRecord',
                'click .btn-clinica': '_onClickDeleteRecord',
                'click .btn-gerencia': '_onClickDeleteRecord',
                'click .btn-soporte': '_onClickDeleteRecord',
                'click .btn-otros': '_onClickDeleteRecord',
            },
            
            _onChangeFilter: function (ev) {
                ev.preventDefault();
                console.log("Desde onChangeFilter " + this.value_filtro);
                this.value_filtro = ev.target.value;
                console.log("Desde onChangeFilter " + this.value_filtro);
                this._updateView(this.value_filtro);
            },
    
            _onClickDeleteRecord: function (ev) {
                ev.preventDefault();
        
                console.log("desde deleteRecord " + ev.currentTarget.id);
                var tienda = ev.currentTarget.id;
    
                this._deleteRecord(tienda);
            },
            
            _deleteRecord: function (tienda) {
                var self = this;
                var reg = "";   
                var zona = "";
                var clave = "borrar_";
                if (this.value_filtro == "reg_tgu") {
                    zona = "TGU";
                    reg = "_tgu";
                } else if (this.value_filtro == "reg_sps") {
                    zona = "SPS";
                    reg = "_sps";
                }
    
                const manejarClickDeleteAdmin = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#admin_value").text(resultado[`admin${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteMegatk = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#megatk_value").text(resultado[`megatk${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteMeditek = (zona, metodo) => {
    
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#meditek_value").text(resultado[`meditek${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteLenka = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#lenka_value").text(resultado[`lenka${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteClinica = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#clinica_value").text(resultado[`clinica${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteGerencia = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#gerencia_value").text(resultado[`gerencia${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteSoporte = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#soporte_value").text(resultado[`soporte${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
                const manejarClickDeleteOtros = (zona, metodo) => {
                    self._rpc({
                        model: 'control.visitas',
                        method: metodo,
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#otros_value").text(resultado[`otros${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
    
                if(tienda == "administracion") {
                    clave = clave + tienda; 
                    manejarClickDeleteAdmin(zona, clave);
                } else if (tienda == "tienda_megatk") {
                    clave = clave + tienda;
                    manejarClickDeleteMegatk(zona, clave);
                } else if (tienda == "tienda_meditek") {
                    clave = clave + tienda;
                    manejarClickDeleteMeditek(zona, clave);
                } else if (tienda == "lenka") {
                    clave = clave + tienda;
                    manejarClickDeleteLenka(zona, clave);
                } else if (tienda == "clinica") {
                    clave = clave + tienda;
                    manejarClickDeleteClinica(zona, clave);
                } else if (tienda == "gerencia") {
                    clave = clave + tienda;
                    manejarClickDeleteGerencia(zona, clave);
                } else if (tienda == "soporte") {
                    clave = clave + tienda;
                    manejarClickDeleteSoporte(zona, clave);
                } else if (tienda == "otros") {
                    clave = clave + tienda;
                    manejarClickDeleteOtros(zona, clave);
                }
            },
    
            _updateView: function (value_filtro) {
                var self = this;
                var reg = "";
    
                if(value_filtro == "reg_tgu") {
                    reg = "_tgu";
                    self._updateUI(reg);
                    
                } else if(value_filtro == "reg_sps") {
                    reg = "_sps";
                    self._updateUI(reg);
                }
            },
    
            _updateUI: function (reg) {
                var self = this;
            
                // Definir funciones con nombre para manejar los eventos click
                const manejarClickAdminState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    console.log("filtro dias " + self.filtro_dias);
                    
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_administracion',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        console.log( "value antes " + self.$el.find("#admin_value").text());
                        console.log("resultado " + resultado[`admin${reg}`]);
                        self.$el.find("#admin_value").text(resultado[`admin${reg}`]);
                        console.log("value despues " +  self.$el.find("#admin_value").text());
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickMegatkState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_tienda_megatk',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#megatk_value").text(resultado[`megatk${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickMeditekState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_tienda_meditek',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#meditek_value").text(resultado[`meditek${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickLenkaState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_lenka',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#lenka_value").text(resultado[`lenka${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickClinicaState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_clinica',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#clinica_value").text(resultado[`clinica${reg}`]);
                        console.log("result clinica " + resultado[`clinica${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickGerenciaState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_gerencia',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#gerencia_value").text(resultado[`gerencia${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickSoporteState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_soporte',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#soporte_value").text(resultado[`soporte${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                const manejarClickOtrosState = () => {
                    var zona = reg == "_tgu" ? "TGU" : "SPS";
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_otros',
                        args: [zona, self.filtro_dias],
                    }).then(function (resultado) {
                        self.$el.find("#otros_value").text(resultado[`otros${reg}`]);
                    }).catch(function (error) {
                        console.error(error);
                    });
                }
            
                // Obtener los datos iniciales
                ajax.rpc(`/control_visitas${reg}`).then(function (result) {
    
                    console.log("Desde updateui " + reg);
                    
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
                    
                    console.log("Desde updateui " + result.admin);
                    console.log("Desde updateui " + result.meditek);
                    console.log("Desde updateui " + result.lenka);
                    console.log("Desde updateui " + result.clinica);
                    console.log("Desde updateui " + result.megatk);
                    console.log("Desde updateui " + result.gerencia);
                    console.log("Desde updateui " + result.soporte);
                    console.log("Desde updateui " + result.otros);
                    
            
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
                        self.filtro_dias = val_filter;
                        if (val_filter == `this_day${reg}`) {
                            
                            ajax.rpc(`/control_visitas_dia${reg}`).then(function (result) {
                                self.$el.find("#admin_value").text(result.admin);
                                self.$el.find("#meditek_value").text(result.meditek);
                                self.$el.find("#lenka_value").text(result.lenka);
                                self.$el.find("#clinica_value").text(result.clinica);
                                self.$el.find("#megatk_value").text(result.megatk);
                                self.$el.find("#gerencia_value").text(result.gerencia);
                                self.$el.find("#soporte_value").text(result.soporte);
                                self.$el.find("#otros_value").text(result.otros);   
                            });
                        } else if (val_filter == `this_week${reg}`) {
                            ajax.rpc(`/control_visitas_semana${reg}`).then(function (result) {
                                self.$el.find("#admin_value").text(result.admin);
                                self.$el.find("#meditek_value").text(result.meditek);
                                self.$el.find("#lenka_value").text(result.lenka);
                                self.$el.find("#clinica_value").text(result.clinica);
                                self.$el.find("#megatk_value").text(result.megatk);
                                self.$el.find("#gerencia_value").text(result.gerencia);
                                self.$el.find("#soporte_value").text(result.soporte);
                                self.$el.find("#otros_value").text(result.otros);
                            });
                        } else if (val_filter == `this_month${reg}`) {
                            ajax.rpc(`/control_visitas_mes${reg}`).then(function (result) {
                                self.$el.find("#admin_value").text(result.admin);
                                self.$el.find("#meditek_value").text(result.meditek);
                                self.$el.find("#lenka_value").text(result.lenka);
                                self.$el.find("#clinica_value").text(result.clinica);
                                self.$el.find("#megatk_value").text(result.megatk);
                                self.$el.find("#gerencia_value").text(result.gerencia);
                                self.$el.find("#soporte_value").text(result.soporte);
                                self.$el.find("#otros_value").text(result.otros);
                            });
                        } else if (val_filter == `this_year${reg}`) {
                            ajax.rpc(`/control_visitas_anio${reg}`).then(function (result) {
                                self.$el.find("#admin_value").text(result.admin);
                                self.$el.find("#meditek_value").text(result.meditek);
                                self.$el.find("#lenka_value").text(result.lenka);
                                self.$el.find("#clinica_value").text(result.clinica);
                                self.$el.find("#megatk_value").text(result.megatk);
                                self.$el.find("#gerencia_value").text(result.gerencia);
                                self.$el.find("#soporte_value").text(result.soporte);
                                self.$el.find("#otros_value").text(result.otros);
                            });
                        }
                    });
                });
            },
    
            start: function () {
                var self = this;
    
                ajax.rpc('/control_visitas_user_reg').then(function (result) {
                    if(result.user_email != 'lmoran@megatk.com' || result.user_email != 'areyes@megatk.com') {
                        if(result.user_reg == "3") {
                            self.$el.find("#filter_region").val("reg_tgu");
                        } else if(result.user_reg == "2") {
                            self.$el.find("#filter_region").val("reg_sps");
                        }
                        console.log("Desde start rpc elemento " + self.$el.find("#filter_region").val());
                        
                        self.value_filtro = self.$el.find("#filter_region").val();
                        self.filtro_dias = self.$el.find("#filter_selection").val();
                        console.log("Desde start rpc value " + self.value_filtro + " filtro " + self.filtro_dias);
                        self._updateView(self.value_filtro);
                    } else {
                        self.$el.find("#filter_region").prop('disabled', false);
                        self.value_filtro = 'reg_tgu';
                        self._updateView(self.value_filtro);
                        
                    }
                })
    
                return this._super.apply(this, arguments);
                        
            },
        })
        core.action_registry.add('control_visitas_tag', CustomDashboard);
        return CustomDashboard;
    });
    