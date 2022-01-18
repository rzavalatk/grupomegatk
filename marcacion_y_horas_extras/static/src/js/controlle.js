odoo.define(
  "marcacion_y_horas_extras.hr_employee_markings_assets",
  function (require) {
    "use strict";

    const myExcelXML = require("excel.xml")
    var core = require("web.core");
    var ListController = require("web.ListController");
    var QWeb = core.qweb;

    ListController.include({
      renderButtons: function ($node) {
        var self = this;
        self._super($node);
        self.$buttons
          .find("#inside_marcking")
          .click(self.proxy("tree_view_action"));
        self.$buttons
          .find("#generate_xhour")
          .click(self.proxy("generate_report_hours_xtra"));
      },
      tree_view_action: function () {
        let fileName = "plantilla-para-importar"
        let col = [{
          'Fecha': '',
          'Nombre': '',
          'Hora': '',
        }]
        var XML = new myExcelXML(col, fileName);
        XML.downLoad();
        location.reload();
        // var self = this;
        // self
        //   ._rpc({
        //     model: "hr.employee.markings",
        //     method: "open_wizard",
        //     args: [],
        //   })
        //   .then(function (e) {
        //     self.do_action(e);
        //   });
      },
      generate_report_hours_xtra: function () { 
        var self = this;
        self
          ._rpc({
            model: "hr.employee.markings",
            method: "open_generate_hours_xtra",
            args: [],
          })
          .then(function (e) {
            self.do_action(e);
          });
      },
    });
  }
);
