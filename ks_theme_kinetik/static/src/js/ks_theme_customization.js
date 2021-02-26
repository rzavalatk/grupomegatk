odoo.define('ks_theme_customization_pop_up', function (require) {
    'use strict'
    var ks_websiteTheme = require('website.theme');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var ColorpickerDialog = require('web.colorpicker');
    var qweb = core.qweb;

    var ThemeCustomizeDialog = ks_websiteTheme.include({

         start:function(){
            var ks_self = this;
            this.viewName = $(document.documentElement).data('view-xmlid');
            var $def_color = this._ksGetThemeColor();
            var $def_themecolor = this._ksGetThemeTextColor();
            var $def_color1 = this._ksGetbgColor();
            var $def_color2 = this._ksGettextColor();
            var $def_radius=this._ksGetRadius();
            var $def_border=this._ksGetBorder();
            var $def_hoverbgcolor=this._ksGethoverbgColor();
            var $def_hovertextcolor=this._ksGethovertextColor();
            var $def_hoverbordercolor=this._ksGetHoverBorderColor();
            var $def = this._ksGetLayouts();
            $def_color.then(function(theme_color){
                ks_self.$el.find("#change_color_theme").spectrum({
                    color: theme_color ,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var themetextcolor=$("#change_textcolor_theme").spectrum('get').toHexString();
                        ks_self._ksonSaveClick(color,themetextcolor);
                    }
                });
               })
               $def_themecolor.then(function(theme_text_color){
                ks_self.$el.find("#change_textcolor_theme").spectrum({
                    color: theme_text_color ,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var themecolor=$("#change_color_theme").spectrum('get').toHexString();
                        ks_self._ksonSaveClickTheme(color,themecolor);
                    }
                });

               })


            $def_color1.then(function(bg_color){
                    ks_self.$el.find("#change_bgcolor").spectrum({
                    color: bg_color ,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var textcolor=$("#change_textcolor").spectrum('get').toHexString();
                        var radius=$("#change_radius").val();
                        var borcolor=$("#change_bordercolor").spectrum('get').toHexString();
                        ks_self._ksonSaveClickbg(color,textcolor,radius,borcolor);
                    }
                });
                })


             $def_color2.then(function(text_color){
                    ks_self.$el.find("#change_textcolor").spectrum({
                    color: text_color ,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var bcolor=$("#change_bgcolor").spectrum('get').toHexString();
                        var radius=$("#change_radius").val();
                         var bordcolor=$("#change_bordercolor").spectrum('get').toHexString();
                        ks_self._ksonSaveClicktext(color,bcolor,radius,bordcolor);
                    }
                });
                })

                $def_border.then(function(border_color){
                    ks_self.$el.find("#change_bordercolor").spectrum({
                    color: border_color ,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var bcolor=$("#change_bgcolor").spectrum('get').toHexString();
                        var tcolor=$("#change_textcolor").spectrum('get').toHexString();
                        var radius=$("#change_radius").val();
                        ks_self._ksonSaveClickborder(color,bcolor,radius,tcolor);
                    }
                });
                })

            $def_radius.then(function(r){

            $("#change_radius").val(r);
            })


            $def_hoverbgcolor.then(function(hover_bg_color){
                    ks_self.$el.find("#change_hoverbgcolor").spectrum({
                    color: hover_bg_color ,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var hovertextcolor=$("#change_hovertextcolor").spectrum('get').toHexString();
                        var hoverbordercolor=$("#change_hoverbordercolor").spectrum('get').toHexString();
                        ks_self._ksonSaveClickhoverbg(color,hovertextcolor,hoverbordercolor);
                    }
                });
                })



             $def_hovertextcolor.then(function(hover_text_color){
                    ks_self.$el.find("#change_hovertextcolor").spectrum({
                    color: hover_text_color,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var hoverbgcolor=$("#change_hoverbgcolor").spectrum('get').toHexString();
                        var hoverbordercolor=$("#change_hoverbordercolor").spectrum('get').toHexString();
                        ks_self._ksonSaveClickhovertext(color,hoverbgcolor,hoverbordercolor);
                    }
                });
                })

                $def_hoverbordercolor.then(function(hover_border_color){
                    ks_self.$el.find("#change_hoverbordercolor").spectrum({
                    color: hover_border_color,
                    preferredFormat: "rgb",
                    showInput: true,
                    showInitial: true,
                    appendTo: $(".o_theme_customize_modal"),
                    change: function(color) {
                        color.toHexString(); // #ff0000
                        var hoverbgcolor=$("#change_hoverbgcolor").spectrum('get').toHexString();
                        var hovertextcolor=$("#change_hovertextcolor").spectrum('get').toHexString();
                        ks_self._ksonSaveClickhoverborder(color,hoverbgcolor,hovertextcolor);
                    }
                });
                })

            ks_self._super();
         },
        _ksGetThemeColor:function(e){
            var ks_scss_path = "/static/src/css/ks_updated_color.scss";
            return $.get("/get/updated/scss", {"scss_path":ks_scss_path})

        },

        _ksGetThemeTextColor:function(e){
            var ks_scss_path = "/static/src/css/ks_updated_color.scss";
            return $.get("/get/updated/scss", {"text_scss_path":ks_scss_path})

        },

         _ksGetbgColor:function(e){
            var ks_button_scss_path="/static/src/css/ks_updated_button_color.scss";
            return $.get("/get/updated/buttonscss", { "bg_scss_path":ks_button_scss_path})
            },

          _ksGettextColor:function(e){
            var ks_button_scss_path="/static/src/css/ks_updated_button_color.scss";
            return $.get("/get/updated/buttonscss", { "text_scss_path":ks_button_scss_path})
            },

            _ksGetRadius:function(e){
            var ks_button_scss_path="/static/src/css/ks_updated_button_color.scss";
            return $.get("/get/updated/buttonscss", { "radius_scss_path":ks_button_scss_path})
            },

            _ksGetBorder:function(e){
            var ks_button_scss_path="/static/src/css/ks_updated_button_color.scss";
            return $.get("/get/updated/buttonscss", { "border_scss_path":ks_button_scss_path})
            },

           _ksGethoverbgColor:function(e){
            var ks_hover_scss_path="/static/src/css/ks_updated_hover_color.scss";
            return $.get("/get/updated/hoverscss", { "hover_bg_scss_path":ks_hover_scss_path})
            },

            _ksGethovertextColor:function(e){
            var ks_hover_scss_path="/static/src/css/ks_updated_hover_color.scss";
            return $.get("/get/updated/hoverscss", { "hover_text_scss_path":ks_hover_scss_path})
            },

            _ksGetHoverBorderColor:function(e){
            var ks_hover_scss_path="/static/src/css/ks_updated_hover_color.scss";
            return $.get("/get/updated/hoverscss", { "hover_border_scss_path":ks_hover_scss_path})
            },

          _ksGetLayouts: function(){
           return  this._rpc({
            route: '/website/get_switchable_related_views',
            params: {
                key: this.viewName,
            },
        }).then(function (result) {
            var currentGroup = '';
            _.each(result, function (item) {
                if (currentGroup !== item.inherit_id[1]) {
                    currentGroup = item.inherit_id[1];
                }
                var $a = $('<a/>', {href: '#', class: 'dropdown-item ks_customize_dropdown_items', 'data-view-id': item.id, role: 'menuitem'})
                            .append(qweb.render('web_editor.components.switch', {id: 'switch-' + item.id, label: item.name}));
                //$a.find('input').prop('checked', !!item.active);
                $('.ks_customize_dropdown_items').find('input').prop('checked', !!item.active);
                $($('.ks_footer_theme').find('input')).attr("checked",false);
                 $($('.ks_button_theme').find('input')).attr("checked",false);
                 $($('.ks_header_theme').find('input')).attr("checked",false);
                 $($('.ks_font_theme').find('input')).attr("checked",false);
                 $($('.ks_box_theme').find('input')).attr("checked",false);
                if (item.key.indexOf('ks_theme_kinetik.custom_header_layout')!= -1){
                 // put this code for any customization and change the image path for what are you previewing
                    var suffix = item.key.match(/\d+/);
                    $a.append("<div class='ks_demo_info_header fa fa-eye' id='ks_info_header"+suffix+"'></div>")
                    if(! $('#ks_img_demo'+suffix) .length){
                        $("#footer").append("<div id='ks_img_demo_header"+suffix+"' class='ks_hover_image_demo'><div class='ks_preview_img'><img src='/ks_theme_kinetik/static/src/img-ui/headers/h-"+suffix+".png'></img><i class='fa fa-times ks_close_demo_preview'></i><div></div>")
                    }
                  $a.find("label").addClass("ks_header_theme")
                  if (item.active){
                            $a.find("label").addClass("ks_header_active")
                           $a.find("input").attr("checked",true)
                    }
                    $(".header_layout_selection").append($a);
                }
                if (item.key.indexOf('ks_theme_kinetik.custom_footer_layout')!= -1){
                    var suffix = item.key.match(/\d+/);
                    $a.append("<div class='ks_demo_info_footer fa fa-eye' id='ks_info_footer"+suffix+"'></div>")
                    if(! $('#ks_img_demo_footer'+suffix) .length){
                        $("#footer").append("<div id='ks_img_demo_footer"+suffix+"' class='ks_hover_image_demo'><div class='ks_preview_img'><img src='/ks_theme_kinetik/static/src/img-ui/footers/f-"+suffix+".png'></img><i class='fa fa-times ks_close_demo_preview'></i><div></div>")
                    }
                     $a.find("label").addClass("ks_footer_theme")
                  if (item.active){
                            $a.find("label").addClass("ks_footer_active")
                           $a.find("input").attr("checked",true)
                    }

                    $(".header_footer_selection").append($a);
                }
                if (item.key.indexOf('ks_theme_kinetik.custom_font_layout')!= -1){
                if(item.key.split('_').splice(-1)>16){
                     var $c='<button type="button" id=font_delete class="btn delete_font" aria-label="Close"><i class="fa fa-times"></i></button>';
                    $a.append($c);}
                     $a.find("label").addClass("ks_font_theme")
                  if (item.active){
                            $a.find("label").addClass("ks_font_active")
                           $a.find("input").attr("checked",true)
                    }
                    $(".header_font_selection").append($a);

                }
                if (item.key.indexOf('ks_theme_kinetik.custom_snippet_width')!= -1){
                    $(".ks_snippet_header").append($a);
                }
                if (item.key.indexOf('ks_theme_kinetik.ks_button_style_layout')!= -1){
                    var end_number=item.key.split('_').slice(-1);
                    var y="<button class='btn' type='submit'>Style "+end_number+"</button>";
                    var $btn = $(y);
                    var x="ks_btn_style_"+end_number;
                    $btn.addClass(x);
                    $a.append($btn);
                    $(".ks_button_selection").append($a);
                     $a.find("label").addClass("ks_button_theme")
                  if (item.active){
                            $a.find("label").addClass("ks_button_active")
                           $a.find("input").attr("checked",true)
                    }
                }
            });
//            click event for font delete
            $(".delete_font").click(function(e){

                    ajax.jsonRpc("/site", 'call', {
                                    'view_id':$(e.currentTarget).parent().data().viewId

                                    }).then(function () {
                   location.reload();
               });
                    });
        });
        },
        _ksonSaveClick:function(color,themetxtcolor){
              var ks_self = this;
              var $ks_theme_color  =  color.toHexString();
              var ks_scss_path = "/static/src/css/ks_updated_color.scss";
              var theme_color = "$theme-color-primary: "+$ks_theme_color+";";
              var themetcolor = "$theme-text-color: "+themetxtcolor+";";
              $.get("/write/updated/scss", {
                        'scss_path': ks_scss_path, 'color': theme_color,'theme_textcolor':themetcolor
               })
          },


           _ksonSaveClickTheme:function(color,themecolor){
              var ks_self = this;
              var $ks_theme_text_color  =  color.toHexString();
              var ks_scss_path = "/static/src/css/ks_updated_color.scss";
              var theme_tcolor = "$theme-text-color: "+$ks_theme_text_color+";";
              var themecolor = "$theme-color-primary: "+themecolor+";";
              $.get("/write/updated/scss", {
                        'scss_path': ks_scss_path, 'theme_color': themecolor,'theme_text_color':theme_tcolor
               })
          },


           _ksonSaveClickbg:function(color,textcolor,radius,border){
              var ks_self = this;
              var $ks_bg_color  =  color.toHexString();
              var ks_button_scss_path= "/static/src/css/ks_updated_button_color.scss";
              var bg_color    = "$btn-primary:" + $ks_bg_color + " !important;";
              var text_color  = "$text-color:"+textcolor+" !important;";
              var button_radius= "$btn-radius:"+radius+"px;";
              var b2_color  = "$btn-border-color:"+border+" !important;";
              $.get("/write/updated/buttonscss", {
                        'scss_path': ks_button_scss_path, 'bgcolor':bg_color, 'bg_textcolor':text_color,'bg_radius':button_radius,'bg_boder_color':b2_color
               })
          },

          _ksonSaveClicktext:function(color,bcolor,radius,b_color){
              var ks_self = this;
              var $ks_text_color=color.toHexString();
              var ks_button_scss_path= "/static/src/css/ks_updated_button_color.scss";
              var text_color  = "$text-color:" + $ks_text_color + " !important;";
              var bgcolor    =   "$btn-primary:" + bcolor + " !important;";
              var button_radius= "$btn-radius:"+radius+"px;";
              var b1color    =   "$btn-border-color:" + b_color + " !important;";
              $.get("/write/updated/buttonscss", {
                        'scss_path': ks_button_scss_path, 'textcolor': text_color, 'text_bgcolor':bgcolor,'text_radius':button_radius,'text_border':b1color
               })
          },


          _ksonSaveClickborder:function(color,bcolor,radius,t_color){
              var ks_self = this;
              var $ks_border_color=color.toHexString();
              var ks_button_scss_path= "/static/src/css/ks_updated_button_color.scss";
              var border_color  = "$btn-border-color:" + $ks_border_color + " !important;";
              var bgcolor    =   "$btn-primary:" + bcolor + " !important;";
              var button_radius= "$btn-radius:"+radius+"px;";
              var t1color    =   "$text-color:" + t_color + " !important;";
              $.get("/write/updated/buttonscss", {
                        'scss_path': ks_button_scss_path, 'bordertexcolor': t1color, 'borderbgcolor':bgcolor,'border_radius':button_radius,'border_color':border_color
               })
          },



          _ksonSaveClickhoverbg:function(color,hovertextcolor,border){
              var ks_self = this;
              var $ks_hover_bg_color=color.toHexString();
              var ks_hover_scss_path= "/static/src/css/ks_updated_hover_color.scss";
              var hover_bgcolor  = "$hover-background:" + $ks_hover_bg_color + " !important;";
              var hover_tcolor    =   "$hover-text-color:" + hovertextcolor + " !important;";
              var hover_bordercolor  = "$hover-border-color:" + border + " !important;";
              $.get("/write/updated/hoverscss", {
                        'scss_path': ks_hover_scss_path, 'hovertcolor': hover_tcolor, 'hover_backgroundcolor':hover_bgcolor,'hover_b_color':hover_bordercolor
               })
          },


          _ksonSaveClickhovertext:function(color,hoverbgcolor,hborder){
              var ks_self = this;
              var $ks_hover_text_color=color.toHexString();
              var ks_hover_scss_path= "/static/src/css/ks_updated_hover_color.scss";
              var hover_textcolor  = "$hover-text-color:" + $ks_hover_text_color + " !important;";
              var hover_bgcolor    =   "$hover-background:" + hoverbgcolor + " !important;";
              var hover_bordercolor  = "$hover-border-color:" + hborder + " !important;";
              $.get("/write/updated/hoverscss", {
                        'scss_path': ks_hover_scss_path, 'hovertextcolor': hover_textcolor, 'hover_bgcolor':hover_bgcolor,'hover_border':hover_bordercolor
               })
          },

            _ksonSaveClickhoverborder:function(color,hoverbgcolor,hovertxtcolor){
              var ks_self = this;
              var $ks_hover_border_color=color.toHexString();
              var ks_hover_scss_path= "/static/src/css/ks_updated_hover_color.scss";
              var hover_bordercolor  = "$hover-border-color:" + $ks_hover_border_color + " !important;";
              var hover_bgcolor    =   "$hover-background:" + hoverbgcolor + " !important;";
              var hover_txtcolor  =   "$hover-text-color:" + hovertxtcolor + " !important;";
              $.get("/write/updated/hoverscss", {
                        'scss_path': ks_hover_scss_path, 'hovertext2color': hover_txtcolor, 'hover_bg2color':hover_bgcolor,'hoverbordercolor':hover_bordercolor
               })
          },




    });
    $(document).on('click', '#saveradius', function (ev) {
             var radius=$("#change_radius").val();
             if(Number(radius)>=0){
             var tcolor=$("#change_textcolor").spectrum('get').toHexString();
             var bcolor=$("#change_bgcolor").spectrum('get').toHexString();
              var bordecolor=$("#change_bordercolor").spectrum('get').toHexString();
             var ks_button_scss_path= "/static/src/css/ks_updated_button_color.scss";
             var text_color  = "$text-color:" +tcolor+" !important;";
             var button_radius= "$btn-radius:"+radius+"px !important;";
             var bgcolor    =   "$btn-primary:" +bcolor+ " !important;";
             var bordercolor    =   "$btn-border-color:" +bordecolor+ " !important;";
             $.get("/write/updated/buttonscss", {
                        'scss_path': ks_button_scss_path, 'tcolor': text_color, 'bcolor':bgcolor,'button_radius':button_radius,'btn_bcolor':bordercolor
               })
               }
               else{
                    alert('Radius should be a Positive Number');

               }

    });



     $(document).on('click', '#reset_all', function (ev) {
                                     ajax.jsonRpc("/reset", 'call'
                                    ).then(function (values) {
                                     var ks_button_scss_path= "/static/src/css/ks_updated_button_color.scss";
                                      var ks_hover_scss_path= "/static/src/css/ks_updated_hover_color.scss";
                                     $.get("/write/updated/hoverscss", {
                        'scss_path': ks_hover_scss_path, 'resethovertextcolor': values['hoverbgcolor'], 'resethover_bgcolor':values['hovertxtcolor'],'resethover_border':values['hoverbordercolor']
                                          })
                                    $.get("/write/updated/buttonscss", {
                                                   'scss_path': ks_button_scss_path, 'resettxtcolor': values['txtcolor'], 'reset_bgcolor':values['bgcolor'],'reset_radius':values['radius'],'resetborder':values['border']
                                                  }).then(function () {
                                                                 location.reload();
                                                                             });
//
               });

     });


       $(document).on('click', '#reset_theme_color', function (ev) {
                                     ajax.jsonRpc("/reset/themecolor", 'call'
                                    ).then(function (value) {
                                     var ks_scss_path= "/static/src/css/ks_updated_color.scss";
                                    $.get("/write/updated/scss", {
                                                   'scss_path': ks_scss_path, 'reset_themetcolor': value['themetxtcolor'], 'reset_themecolor':value['themecolor']
                                                  }).then(function () {
                                                                 location.reload();
                                                                             });
//
               });


     });

     // Reset Headers

    $(document).on('click', '#ks_reset_header', function (ev) {
        ajax.jsonRpc("/reset/header", 'call').then(function () {
            location.reload();
        });
    });

     // Reset Footers

    $(document).on('click', '#ks_reset_footer', function (ev) {
        ajax.jsonRpc("/reset/footer", 'call').then(function () {
            location.reload();
        });
    });


     $(document).on('click','#save_theme_color',function(){

                                                                location.reload();
                 });


      $(document).on('click','#save_color',function(){

                                                                location.reload();
                 });
    $(document).ready(function(){
         $("#theme_customize").on("click", function(){
            $(document).on("shown.bs.modal", "#theme_customize_modal", function(){
                alert();
            });
            $( "#theme_customize_modal" ).on('show.bs.modal', function(){
                alert("I want this to appear after the modal has opened!");
            });
            });
        $(".header_selection_toggle");


    });

//    handling submit of dynamic font loading option
    $(document).on('submit', 'form.myForm', function (ev) {
               var font_url = $(".input_url").val();
               if (font_url.search('family')!=-1)
               {
                 var status;
                 var statusText;
                 var responseText;
                 var state=$.ajax({ url: font_url})
                 state.then(function(){
                    this.status=state.status;
                    this.statusText=state.statusText;
                    this.responseText=state.responseText;
                     if(this.status == 200) //if(statusText == OK)
            {
                 var font_family_name= font_url.split('?')[1].split('=')[1].split(':')[0];
                ajax.jsonRpc("/some_url", 'call', {
                                'css':this.responseText,
                                'url':font_url,
                                'font_family':font_family_name,

                     }).then(function(){

                        location.reload()
                     })

            }
            else{
                    alert('please enter a valid font family name');
            }
                 }.bind(this))

}
            else{
                        alert('please enter a valid font url');
                        }



    });
//  handle the eye icon click to preview the header or footer
    $(document).on("click",'.ks_demo_info_header',function(ev){
      var suffix = $(ev.currentTarget).attr("id").match(/\d+/);
      var ks_img;
      $("#ks_img_demo_header"+suffix).addClass("ks_show_demo_img")
    });
    $(document).on("click",'.ks_demo_info_footer',function(ev){
      var suffix = $(ev.currentTarget).attr("id").match(/\d+/);
      var ks_img;
      $("#ks_img_demo_footer"+suffix).addClass("ks_show_demo_img")
    });
//    Close the preview image from demo
    $(document).on("click",'.ks_close_demo_preview',function(ev){
      $(".ks_show_demo_img").removeClass("ks_show_demo_img")
    })
//   Header toggle  on customize theme
    $(document).on("click",'.ks_header_theme',function(ev){
      var currentT=ev.currentTarget;
      _.each($(".ks_header_theme"),function(ev){
   if(!$(currentT).hasClass('ks_header_active')){
            $(ev).removeClass("ks_header_active")
            }
      })
      if ($(ev.currentTarget).hasClass('ks_header_active')){
                $(ev.currentTarget).removeClass("ks_header_active")}
      else{
      $(ev.currentTarget).addClass('ks_header_active');}
    })

   $(document).on("click",'.ks_footer_theme',function(ev){
         var currentT=ev.currentTarget;
      _.each($(".ks_footer_theme"),function(ev){
            if(!$(currentT).hasClass('ks_footer_active')){
            $(ev).removeClass("ks_footer_active")
            }
      })
       if ($(ev.currentTarget).hasClass('ks_footer_active')){
                $(ev.currentTarget).removeClass("ks_footer_active")
                }
      else{
      $(ev.currentTarget).addClass('ks_footer_active');
      }
    })

    $(document).on("click",'.ks_font_theme',function(ev){
         var currentT=ev.currentTarget;
      _.each($(".ks_font_theme"),function(ev){
       if(!$(currentT).hasClass('ks_font_active')){
            $(ev).removeClass("ks_font_active")
            }
      })
       if ($(ev.currentTarget).hasClass('ks_font_active')){
                $(ev.currentTarget).removeClass("ks_font_active")
                }
      else{
      $(ev.currentTarget).addClass('ks_font_active');
      }
    })

    $(document).on("click",'.ks_button_theme',function(ev){
    var currentT=ev.currentTarget;
      _.each($(".ks_button_theme"),function(ev){
       if(!$(currentT).hasClass('ks_button_active')){
            $(ev).removeClass("ks_button_active")
            }
      })
       if ($(ev.currentTarget).hasClass('ks_button_active')){
                $(ev.currentTarget).removeClass("ks_button_active")
                }
      else{
      $(ev.currentTarget).addClass('ks_button_active');
      }
    })
     $(document).on("mouseenter",'.ks_offer_header_theme',function(ev){
      if ($(ev.currentTarget).hasClass('ks_offer_header_active')){
         $(ev.currentTarget).removeClass("ks_offer_header_active")
      }
      else{
            $(ev.currentTarget).addClass('ks_offer_header_active');
      }
    })
});

