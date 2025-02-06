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

            self.$el.find("#admin_state").click(function () {
                
                // Ejecutar el método en el servidor
                self._rpc({
                    model: 'control.visitas',
                    method: 'visita_administracion',
                    args: [result.admin_name],
                }).then(function (resultado) {
                    // Cargar la vista después de ejecutar el método
                    self.do_action({
                        name: 'Administración',
                        type: 'ir.actions.act_window',
                        res_model: 'control.visitas',
                        view_mode: 'tree,form',
                        views: [[false, 'form'], [control.visitas.view.tree, 'list']],
                        domain: [['name', '=', result.admin_name]],
                    });
                })
              
            })
            self.$el.find("#megatk_state").click(function () {
                self.do_action({
                    name: 'Visitas Tienda MegaTK',
                    type: 'ir.actions.act_window',
                    res_model: 'control.visitas',
                    view_mode: 'tree,form',
                    views: [[false, 'form'],[false, 'list']],
                    domain: [['name', '=', result.megatk_name]],
                })
            })
            self.$el.find("#meditek_state").click(function () {
                self.do_action({
                    name: 'Visitas Tienda Meditek',
                    type: 'ir.actions.act_window',
                    res_model: 'control.visitas',
                    view_mode: 'tree,form',
                    views: [[false, 'form'],[false, 'list']],
                    domain: [['name', '=', result.meditek_name]],
                })
            })
            self.$el.find("#lenka_state").click(function () {
                self.do_action({
                    name: 'Visitas Lenka',
                    type: 'ir.actions.act_window',
                    res_model: 'control.visitas',
                    view_mode: 'tree,form',
                    views: [[false, 'form'],[false, 'list']],
                    domain: [['name', '=', result.lenka_name]],
                })
            })
            self.$el.find("#clinica_state").click(function () {
                self.do_action({
                    name: 'Visitas Clinica',
                    type: 'ir.actions.act_window',
                    res_model: 'control.visitas',
                    view_mode: 'tree,form',
                    views: [[false, 'form'],[false, 'list']],
                    domain: [['name', '=', result.clinica_name]],
                })
            })
        })
    },
})
core.action_registry.add('control_visitas_tag', CustomDashboard);
return CustomDashboard;
});