try {
    let str = "";
    let abc = "abcdefghijklmnopqrstuvwxyz";
    for (let i = 0; i < 4; i++) {
      str += abc.charAt(Math.floor(Math.random() * abc.length));
    }
    odoo.define(`hours.xtra.${str}`, function (require) {
      "use strict";
      const rpc = require("web.rpc");
      var FormRenderer = require("web.FormRenderer");
      const myExcelXML = require("excel.xml");
      let data = {};
  
      FormRenderer.include({
        confirmChange: function (state, id, fields, e) {
          if (fields.length > 0) {
            data[fields[0]] = state.data[fields[0]];
          }
          return this._super.apply(this, arguments);
        },
      });
  
      function rpc_consult(data) {
        rpc
          .query({
            model: "hours.xtras",
            method: "dat_form_custom",
            args: [[data]],
          })
          .done(function (e) {
            if (e) {
              var XML = new myExcelXML(e, `horas_extra_${data.date.format("DD-MM-YYYY")}`);
              XML.downLoad();
              location.reload();
            }
          })
          .fail(function (err) {
            console.warn("ERROR QUERY: (" + err.code + "): " + err.message);
          });
      }
  
      let button = $("#generate_button");
      button.click(function (e) {
        e.preventDefault();
        if (data.employee_ids) {
          let temp = [];
          data.employee_ids.data.forEach((element) => {
            temp.push(element.data.id);
          });
          data.employee_ids = temp;
        }
        rpc_consult(data);
      });
  
      new FormRenderer();
    });
  } catch (error) {
    //   console.log(error);
    location.reload();
  }