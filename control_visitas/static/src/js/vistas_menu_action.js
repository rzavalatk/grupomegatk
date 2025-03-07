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
        this.value_filtro = ev.target.value;
        return value_filtro
    },

    start: function () {
        
        var val = this.value_filtro;
        var self = this;
        console.log(val);

        if (val == "reg_tgu") {
            ajax.rpc('/control_visitas_tgu').then(function (result) {
                self.$el.find("#admin_value").text(result.admin);
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
    
                self.$el.find("#filter_selection").change(function(e) {
                    
                    var target = $(e.target)
                    var value = target.val()
                    var val_filter = value + "_tgu"
    
                    if (val_filter == "this_day_tgu") {
                        
                        ajax.rpc('/control_visitas_dia_tgu').then(function(result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                            console.log(e)
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
                    } else if (val_filter == "this_week_tgu") {
                        ajax.rpc('/control_visitas_semana_tgu').then(function (result) {
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
                    } else if (val_filter == "this_month_tgu") {
                        ajax.rpc('/control_visitas_mes_tgu').then(function (result) {
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
                    } else if (val_filter == "this_year_tgu") {
                        ajax.rpc('/control_visitas_anio_tgu').then(function (result) {
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
            })//final filter
        }

        if (val == "reg_sps") {
            ajax.rpc('/control_visitas_sps').then(function (result) {
                self.$el.find("#admin_value").text(result.admin);
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
    
                self.$el.find("#filter_selection").change(function(e) {
                    
                    var target = $(e.target)
                    var value = target.val()
                    var val_filter = value + '_sps'
    
                    if (val_filter == "this_day_sps") {
                        ajax.rpc('/control_visitas_dia_sps').then(function(result) {
                            self.$el.find("#admin_value").text(result.admin);
                            self.$el.find("#meditek_value").text(result.meditek);
                            self.$el.find("#lenka_value").text(result.lenka);
                            self.$el.find("#clinica_value").text(result.clinica);
                            self.$el.find("#megatk_value").text(result.megatk);
                            console.log(e)
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
                    } else if (val_filter = "this_week_sps") {
                        ajax.rpc('/control_visitas_semana_sps').then(function (result) {
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
                    } else if (val_filter = "this_month_sps") {
                        ajax.rpc('/control_visitas_mes_sps').then(function (result) {
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
                    } else if (val_filter = "this_year_sps") {
                        ajax.rpc('/control_visitas_anio_sps').then(function (result) {
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
            })//final filter
        }//final filtro region          
    },
})
core.action_registry.add('control_visitas_tag', CustomDashboard);
return CustomDashboard;
});

