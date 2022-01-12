try {
  let str = "";
  let abc = "abcdefghijklmnopqrstuvwxyz";
  for (let i = 0; i < 4; i++) {
    str += abc.charAt(Math.floor(Math.random() * abc.length));
  }
  odoo.define(`marking.assets-${str}`, function (require) {
    "use strict";
    const rpc = require("web.rpc");
    var FormRenderer = require("web.FormRenderer");
    const myExcelXML = require("excel.xml")
    let data = {};

    FormRenderer.include({
      confirmChange: function (state, id, fields, e) {
        if (fields.length > 0) {
          data[fields[0]] = state.data[fields[0]];
        }
        return this._super.apply(this, arguments);
      },
    });

    let button = $("#generate_button");
    $("#go").click(function (e) {
      e.preventDefault();
      location.reload();
    });

    function rpc_consult(data) {
      rpc
        .query({
          model: "making.inside",
          method: "create_marking",
          args: [[data]],
        })
        .done(function (e) {
          if (e) {
            let fileName = data.date 
              ? `marcaciones_${data.date.format("DD-MM-YYYY")}`
              : `marcaciones_${data.date_init.format("DD-MM-YYYY")}-to-${data.date_end.format("DD-MM-YYYY")}`
            var XML = new myExcelXML(e, fileName);
            XML.downLoad();
            location.reload();
          }
        })
        .fail(function (err) {
          console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
        });
    }

    button.click(function (e) {
      e.preventDefault();
      if (data.marking_ids) {
        let temp = [];
        data.marking_ids.data.forEach((element) => {
          temp.push(element.data.id);
        });
        data.marking_ids = temp;
      }
      if (data.more_one_day) {
        if (data.date_end > data.date_init) {
          rpc_consult(data);
        } else {
          $("#hidden_box").modal("show");
        }
      } else {
        rpc_consult(data);
      }
    });

    new FormRenderer();
  });
} catch (error) {
  //   console.log(error);
  location.reload();
}
