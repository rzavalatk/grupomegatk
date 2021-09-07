$(document).ready(function () {
  "use strict";
  try {
    let $signatureField = $("#sign_area");
    let $clearButton = $("#clear_button");
    let $saveButton = $("#write");
    let id = document.getElementsByName("id");
    if (id.length > 0) {
      id = id.item(0);
    } else {
      id = false;
    }

    $clearButton.click(function (e) {
      e.preventDefault();
      $signatureField.jSignature("reset");
      $saveButton.prop("disabled", true);
      let alert = document.getElementById("alert");
      alert.innerHTML = "";
      alert.innerHTML = `<div class="alert alert-danger" role="alert">
                              Esperando firma...
                          </div>`;
    });

    let width = $signatureField.width();
    let height = width > 500 ? width * 0.29 : width * 0.80;

    $signatureField.empty().jSignature({
      "decor-color": "transparent",
      "background-color": "#FFF",
      color: "#000",
      lineWidth: 2,
      width: width,
      height: height,
    });

    //Listeners
    let signatureElement = document.getElementById("sign_area");
    function action() {
      if (id) {
        $saveButton.prop("disabled", false);
      }
      let alert = document.getElementById("alert");
      alert.innerHTML = "";
      alert.innerHTML = `<div class="alert alert-success" role="alert">
                            Firma capturada correctamente
                          </div>`;
    };
    signatureElement.addEventListener("touchstart", action);
    signatureElement.addEventListener("click", action);
    //

    $saveButton.click(function (e) {
      e.preventDefault();
      let str = "";
      let abc = "abcdefghijklmnopqrstuvwxyz";
      for (let i = 0; i < 4; i++) {
        str += abc.charAt(Math.floor(Math.random() * abc.length));
      }
      try {
        odoo.define(`sign_documents.signing-${str}`, function (require) {
          "use strict";

          const rpc = require("web.rpc");

          let sign = $signatureField.jSignature("getData", "image")[1];
          let idInt = id.innerHTML.replace(/[,]/g, "");

          rpc
            .query({
              model: "stock.picking",
              method: "write",
              args: [
                [parseInt(idInt)],
                {
                  sign: sign,
                  passed: "Si",
                },
              ],
            })
            .done(function (data) {
              if (data) {
                return data;
              }
            })
            .fail(function (e) {
              console.log("Error", e);
            });
        });
      } catch (error) {
        // console.log(error);
        location.reload();
      }
    });
  } catch (error) {
    // console.log(error);
    location.reload();
  }
});
