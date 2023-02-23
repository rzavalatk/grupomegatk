odoo.define("account_comisiones.assets_js", (require) => {
  "use strict";
  var FormController = require("web.FormController");
  const rpc = require("web.rpc");
  const myExcelXML = require("excel.xml");

  var formController = FormController.include({
    _onButtonClicked: function (event) {
      if (event.data.attrs.id === "create_excel") {
        rpc
          .query({
            model: "account.comisiones",
            method: "generate_excel",
            args: [[event.data.record.res_id]],
          })
          .done(function (e) {
            if (e) {
                var XML = new myExcelXML(e.data,e.name);
                XML.downLoad();
                location.reload();
              }
          })
          .fail(function (err) {
            alert("ERROR QUERY: (" + err.code + "): " + err.message);
            // location.reload();
          });
      }
      this._super(event);
    },
  });

  return formController;
});
