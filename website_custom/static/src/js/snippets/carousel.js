odoo.define("carousel.front", ["web.ajax"], (require) => {
  "use strict";
  const ajax = require("web.ajax");

  const getStyle = (style, image, i) => {
    switch (style) {
      case "1":
        return `
        <div class="carousel-item oe_custom_bg oe_img_bg py-5 ${
          i === 0 ? " active" : ""
        }" style="background-image: url('data:image/jpg;base64,${
          image.image
        }'); backgroundRepeat: no-repeat !important;
        backgroundPosition: center center !important;
        backgroundSize: cover !important;" 
        data-name="Slide">
          <div class="container mt-5">
              <div class="row content">
                  <div class="carousel-content col-lg-6 offset-lg-6">
                      <h2>
                          <font style="font-size: 62px; 
                          -webkit-text-fill-color: ${image.font_color_name};
                          ${
                            image.stroke_name
                              ? `-webkit-text-stroke: ${image.size_stroke_name}px ${image.color_stroke_name};`
                              : ""
                          }" 
                          class="o_default_snippet_text">${
                            image.name ? image.name : ""
                          }</font>
                      </h2>
                      <h4>
                          <font style="
                          -webkit-text-fill-color: ${
                            image.font_color_description
                          };
                          ${
                            image.stroke_description
                              ? `-webkit-text-stroke: 1px ${image.color_stroke_description};`
                              : ""
                          }" class="o_default_snippet_text">${
          image.description ? image.description : ""
        }</font>
                      </h4>
                      <div class="s_btn text-left pt16 pb16" data-name="Buttons">
                          <a href="/shop/product/${
                            image.product_id
                          }?min=120.0&ppg=24&max=25000.0" class="btn btn-primary  o_default_snippet_text">${
          image.label_button ? image.label_button : ""
        }</a>
                      </div>
                  </div>
              </div>
          </div>
        </div>
      `;
      case "2":
        return `
        <div class="carousel-item oe_custom_bg oe_img_bg py-5${
          i === 0 ? " active" : ""
        }" style="background-image: url('data:image/jpg;base64,${
          image.image
        }');" data-name="Slide">
          <div class="container mt-5">
              <div class="row content">
                  <div class="carousel-content col-lg-7">
                      <div class="s_title pb8" data-name="Title">
                          <h2 class="s_title_default">
                              <font style="font-size: 62px;
                              -webkit-text-fill-color: ${image.font_color_name};
                          ${
                            image.stroke_name
                              ? `-webkit-text-stroke: ${image.size_stroke_name}px ${image.color_stroke_name};`
                              : ""
                          }" class="o_default_snippet_text">${
          image.name ? image.name : ""
        }</font>
                          </h2>
                      </div>
                      <h4>
                          <font style="
                          -webkit-text-fill-color: ${
                            image.font_color_description
                          };
                          ${
                            image.stroke_description
                              ? `-webkit-text-stroke: 1px ${image.color_stroke_description};`
                              : ""
                          } class="o_default_snippet_text">${
          image.description ? image.description : ""
        }</font>
                      </h4>
                      <div class="s_btn text-left pt16 pb16" data-name="Buttons">
                          <a href="/shop/product/${
                            image.product_id
                          }?min=120.0&ppg=24&max=25000.0" class="btn btn-primary  o_default_snippet_text">${
          image.label_button ? image.label_button : ""
        }</a>
                      </div>
                  </div>
              </div>
          </div>
      </div>
        `;
      case "3":
        return `
          <div class="carousel-item oe_custom_bg oe_img_bg py-5 ${
            i === 0 ? " active" : ""
          }" data-name="Slide">
            <img class="d-block w-100" src="data:image/jpg;base64,${image.image}" alt="${image.name}">
          </div>
          `;
      default:
        return "";
    }
  };

  $(document).ready(() => {
    const myCarousel = document.getElementById("my-carousel-content");
    if (myCarousel) {
      ajax.jsonRpc("/get_images_carousel").then((data) => {
        if (data.length > 0) {
          myCarousel.innerHTML = "";
          let i = 0;
          for (const image of data) {
            const htmlCustom = getStyle(image.style, image, i);
            myCarousel.innerHTML += htmlCustom;
            i += 1;
          }
        }
      });
    }
  });
});
