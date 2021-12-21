odoo.define(
  "marcacion_y_horas_extras.hr_employee_markings_assets",
  function (require) {
    "use strict";

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
      },
      tree_view_action: function () {
        var self = this;
        self
          ._rpc({
            model: "hr.employee.markings",
            method: "open_wizard",
            args: [],
          })
          .then(function (csv) {
            self.do_action(csv);
          });
      },
    });
  }
);
