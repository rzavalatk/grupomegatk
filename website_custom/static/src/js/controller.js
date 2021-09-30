odoo.define("breadcum_custom.front", ["web.ajax", "web.rpc"], (require) => {
  "use strict";
  const ajax = require("web.ajax");

  $(document).ready(() => {
    let section = document.getElementById("section_breadcum");
    let a = document.getElementsByTagName("a");
    let sold_out = document.getElementById("sold_out")
    for (const i of a) {
      if (i.id === "add_to_cart") {
        i.style.display = "none";
      }
    }
    //
    let idProduct = window.location.pathname.split("-")
    idProduct = parseInt(idProduct[idProduct.length-1])
    if (!isNaN(idProduct)) {
      ajax.jsonRpc("/get_quantity", "call", {product: idProduct}).then(function (data) {
          if (data.quantity > 0) {
            for (const i of a) {
              if (i.id === "add_to_cart") {
                i.style.display = "block";
              }
            }
          }else{
            sold_out.style.display = "block"
          }
        })
    }
    //
    if (section) {
      ajax.jsonRpc("/get_images_breadcum").then((data) => {
        if (data.image) {
          section.style.backgroundImage = `url('data:image/png;base64,${data.image}')`;
          section.style.backgroundRepeat = "no-repeat";
          section.style.backgroundPosition = "center center";
          section.style.backgroundSize = "cover";
        }
      });
    }
  });
});
