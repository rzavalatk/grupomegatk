odoo.define("website_custom.video_web", function (require) {
  "use strict";
  const ajax = require("web.ajax");
  var $document = $(document);

  function register_video(index, pathname) {
    ajax
      .jsonRpc("/set_video_web", "call", { index: index, path: pathname })
      .then((data) => {
        if (data) {
          location.reload();
        }
      });
  }

  function stamp_video(snippets, videos) {
    var i = 0;
    while (i < snippets.length) {
      var j = 0;
      var snippet = snippets[i];
      while (j < videos.length) {
        var video = videos[j];
        if (video.url) {
          if (parseInt(video.position) === i) {
            snippet.innerHTML = "";
            snippet.innerHTML = `
            <div class="row justify-content-md-center">
            <div class="video_web_no_found">
            <iframe width="${video.width ? video.width : 500}" height="${video.height ? video.height : 500}" src="https://www.youtube.com/embed/${video.url}" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen="True"/>
            </div>
            </div>
            `;
          }
        }else{
          try {
            var link = snippet.getElementsByTagName("a")
            link.item(0).href = `${location.origin}/web#id=${video.id}&action=1026&model=video.web&view_type=form&menu_id=655`
          } catch (error) {}
        }
        j++;
      }
      i++;
    }
  }

  $document.ready(function () {
    var URLactual = window.location.pathname;
    const video_web = document.getElementsByClassName("video_web");
    ajax.jsonRpc("/get_video_web", "call", { url: URLactual }).then((data) => {
      switch (true) {
        case video_web.length > data.length:
          var index = 0;
          while (index < video_web.length) {
            register_video(index, URLactual);
            ++index;
          }
          break;

        case video_web.length < data.length:
          stamp_video(video_web, data);
          break;

        case video_web.length === data.length:
          stamp_video(video_web, data);
          break;

        default:
          break;
      }
    });
  });
});
