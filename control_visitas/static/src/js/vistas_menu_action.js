odoo.define('control_visitas.visitas_menu_action', function (require) {
    "use strict";
    
    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var ajax = require('web.ajax');
    var CustomDashboard = AbstractAction.extend({
        template: 'VisitasMenuDashboard',
    
        start: function () {
            var self = this;
            ajax.rpc('/control_visitas').then(function (result) {
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
    
                    if (value == "this_day") {
                        ajax.rpc('/control_visitas_dia').then(function(result) {
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
                    } else if (value = "this_week") {
                        ajax.rpc('/control_visitas_semana').then(function (result) {
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
                    } else if (value = "this_month") {
                        ajax.rpc('/control_visitas_mes').then(function (result) {
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
                    } else if (value = "this_year") {
                        ajax.rpc('/control_visitas_anio').then(function (result) {
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
        },
    })
    core.action_registry.add('control_visitas_tag', CustomDashboard);
    return CustomDashboard;
    });