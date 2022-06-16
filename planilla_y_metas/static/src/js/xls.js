try {
  let str = "";
  let abc = "abcdefghijklmnopqrstuvwxyz";
  for (let i = 0; i < 4; i++) {
    str += abc.charAt(Math.floor(Math.random() * abc.length));
  }
  odoo.define(`metas.export.${str}`, "excel.xml", function (require) {
    "use strict";
    const rpc = require("web.rpc");
    const myExcelXML = require("excel.xml");

    let id = document.getElementsByName("id");
    let name = document.getElementsByName("name");
    if (id.length > 0) {
      id = id.item(0);
    } else {
      id = false;
    }
    if (name.length > 0) {
      name = name.item(0).innerHTML;
    } else {
      name = false;
    }
    let idInt = id.innerHTML.replace(/[,]/g, "");
    var excel = $("#export");

    excel.click(function (e) {
      e.preventDefault();
      rpc_consult();
    });

    function rpc_consult() {
      rpc
        .query({
          model: "hr.employee",
          method: "csv_download",
          args: [[parseInt(idInt)]],
        })
        .done(function (e) {
          if (e) {
            var XML = new myExcelXML(e, name);
            XML.downLoad();
            location.reload();
          }
        })
        .fail(function (err) {
          console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
        });
    }
  });
} catch (error) {
  //   console.log(error);
  location.reload();
}
