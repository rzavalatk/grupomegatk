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
            console.log(this.value_filtro);
            this.value_filtro = ev.target.value;
            console.log(this.value_filtro);
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
            ajax.rpc(`/control_visitas${reg}`).then(function (result) {
                self.$el.off();
                // self.$el.find("#admin_value").text(result.admin);
                self.$el.find("#meditek_value").text(result.meditek);
                self.$el.find("#lenka_value").text(result.lenka);
                self.$el.find("#clinica_value").text(result.clinica);
                self.$el.find("#megatk_value").text(result.megatk);
                self.$el.find("#gerencia_value").text(result.gerencia);
                self.$el.find("#soporte_value").text(result.soporte);
                self.$el.find("#otros_value").text(result.otros);
    
                self.$el.find("#admin_state").click(function () {
                    // Ejecutar el método en el servidor
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_administracion',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el self.reload();
                        self.$el.find("#admin_value").text(resultado['admin_tgu']);
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#megatk_state").click(function () {
                    // Ejecutar el método en el servidor
                    self._rpc({
                        model: 'control.visitas',
                        method: 'visita_tienda_megatk',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#meditek_state").click(function () {
                        // Ejecutar el método en el servidor
                        self._rpc({
                        model: 'control.visitas',
                        method: 'visita_tienda_meditek',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#lenka_state").click(function () {
                        // Ejecutar el método en el servidor
                        self._rpc({
                        model: 'control.visitas',
                        method: 'visita_lenka',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#clinica_state").click(function () {
                        // Ejecutar el método en el servidor
                        self._rpc({
                        model: 'control.visitas',
                        method: 'visita_clinica',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#gerencia_state").click(function () {
                        // Ejecutar el método en el servidor
                        self._rpc({
                        model: 'control.visitas',
                        method: 'visita_gerencia',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#soporte_state").click(function () {
                        // Ejecutar el método en el servidor
                        self._rpc({
                        model: 'control.visitas',
                        method: 'visita_soporte',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
                self.$el.find("#otros_state").click(function () {
                        // Ejecutar el método en el servidor
                        self._rpc({
                        model: 'control.visitas',
                        method: 'visita_otros',
                        args: [result.admin_name],
                    }).then(function (resultado) {
                        // Cargar la vista después de ejecutar el método
                        window.location.reload();
                        
                    }).catch(function (error) {
                        // Manejar el error
                        console.error(error);
                    });
                })
    
                self.$el.find("#filter_selection").change(function(e) {
                    
                    var target = $(e.target)
                    var value = target.val()
                    var val_filter = value + reg
    
                    if (val_filter == `this_day${reg}`) {
                        
                        ajax.rpc(`/control_visitas_dia${reg}`).then(function(result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                            self.$el.find("#admin_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_administracion',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el self.reload();
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#megatk_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_megatk',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#meditek_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_meditek',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#lenka_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_lenka',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#clinica_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_clinica',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#gerencia_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_gerencia',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#soporte_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_soporte',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#otros_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_otros',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                        })
                    } else if (val_filter == `this_week${reg}`) {
                        ajax.rpc(`/control_visitas_semana${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
    
                            self.$el.find("#admin_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_administracion',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el self.reload();
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#megatk_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_megatk',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#meditek_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_meditek',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#lenka_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_lenka',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#clinica_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_clinica',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#gerencia_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_gerencia',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#soporte_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_soporte',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#otros_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_otros',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                        })
                    } else if (val_filter == `this_month${reg}`) {
                        ajax.rpc(`/control_visitas_mes${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
    
                            self.$el.find("#admin_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_administracion',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el self.reload();
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#megatk_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_megatk',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#meditek_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_meditek',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#lenka_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_lenka',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#clinica_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_clinica',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#gerencia_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_gerencia',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#soporte_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_soporte',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#otros_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_otros',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                        })
                    } else if (val_filter == `this_year${reg}`) {
                        ajax.rpc(`/control_visitas_anio${reg}`).then(function (result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
    
                            self.$el.find("#admin_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_administracion',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el self.reload();
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#megatk_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_megatk',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#meditek_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_tienda_meditek',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#lenka_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_lenka',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#clinica_state").click(function () {
                                    // Ejecutar el método en el servidor
                                    self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_clinica',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#gerencia_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_gerencia',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#soporte_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_soporte',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                            self.$el.find("#otros_state").click(function () {
                                // Ejecutar el método en el servidor
                                self._rpc({
                                    model: 'control.visitas',
                                    method: 'visita_otros',
                                    args: [result.admin_name],
                                }).then(function (resultado) {
                                    // Cargar la vista después de ejecutar el método
                                    window.location.reload();
                                    
                                }).catch(function (error) {
                                    // Manejar el error
                                    console.error(error);
                                });
                            })
                        })
                    }
                })
            });    
        },

        start: function () {
            var self = this;

            this._updateView();
            self.value_filtro = self.$el.find("#filter_selection").val();
            return this._super.apply(this, arguments);
                    
        },
    })
    core.action_registry.add('control_visitas_tag', CustomDashboard);
    return CustomDashboard;
});
