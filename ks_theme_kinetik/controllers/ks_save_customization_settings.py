from odoo import http
from odoo.http import request
import os
from string import punctuation
import base64
from lxml import etree, html
import uuid


class WebsiteShopBrands(http.Controller):
    # Fixme-  Find a way to save customization settings in attachment

    @http.route([
        '/write/updated/scss',
    ], type='http', auth="public", website=True)
    def KsWriteUpdatedScss(self, **kw):
        bundle_xmlid = 'web.assets_common'
        ks_scss_path = kw.get('scss_path', False)
        if kw.get('color',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(("%s\n%s" % (kw.get('color', False), kw['theme_textcolor'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.theme_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()

        elif kw.get('theme_text_color',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(("%s\n%s" % (kw.get('theme_color', False), kw['theme_text_color'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.theme_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        elif kw.get('reset_themetcolor',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(("%s\n%s" % (kw['reset_themecolor'], kw['reset_themetcolor'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.theme_create_attach_and_view(ks_custom_url, datas,ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        return None

    def theme_create_attach_and_view(self, ks_custom_url, datas, ks_scss_path):
        KsIrAttachment = request.env["ir.attachment"]
        _create_attach = {
            'name': ks_custom_url,
            'type': "binary",
            'mimetype': "text/scss",
            'datas': datas,
            'datas_fname': ks_scss_path.split("/")[-1],
            'url': ks_custom_url,
        }
        website = request.env['website'].get_current_website()
        _create_attach.update({
            'website_id': website.id,
        })
        KsIrAttachment.create(_create_attach)
        _KsIrUiView = request.env["ir.ui.view"]
        _ks_view_to_xpath = request.env['ir.ui.view'].search(
            [('key', '=', 'ks_theme_kinetik._ks_assets_primary_variables')], limit=1)

        create_view = {
            'name': ks_custom_url,
            'key': 'ks_theme_kinetik.scss_%s' % str(uuid.uuid4())[:6],
            'mode': "extension",
            'priority': 1,
            'inherit_id': _ks_view_to_xpath.id,
            'arch': """
                         <data inherit_id="%(inherit_xml_id)s" name="%(name)s">
                             <xpath expr="//link[@href='%(url_to_replace)s']" position="attributes">
                                 <attribute name="href">%(new_url)s</attribute>
                             </xpath>
                         </data>
                     """ % {
                'inherit_xml_id': _ks_view_to_xpath.xml_id,
                'name': ks_custom_url,
                'url_to_replace': '/' + 'ks_theme_kinetik' + ks_scss_path,
                'new_url': ks_custom_url,
            }
        }
        website = request.env['website'].get_current_website()
        create_view.update({
            'website_id': website.id,
        })
        _KsIrUiView.create(create_view)

    def _ks_custom_scss_file_url(self, url, bundle):
        parts = url.rsplit(".", 1)
        return "%s.custom.%s.%s" % (parts[0], bundle, parts[1])

    def _ks_get_attachment(self, ks_custom_url, op='='):
        assert op in ('=like', '='), 'Invalid operator'
        KsIrAttachment = request.env["ir.attachment"]
        website = request.env['website'].get_current_website()
        return KsIrAttachment.search([("url", op, ks_custom_url), ('website_id', '=', website.id)])

    @http.route([
        '/write/updated/buttonscss',
    ], type='http', auth="public", website=True)
    def KsWriteUpdatedButtonScss(self, **kw):
        bundle_xmlid = 'web.assets_common'
        ks_scss_path = kw.get('scss_path', False)
        if kw.get('textcolor',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s\n%s" % (kw['text_bgcolor'],
                                     kw['textcolor'], kw['text_border'], kw['text_radius'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.button_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        elif kw.get('bgcolor',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s\n%s" % (kw['bgcolor'],
                                     kw['bg_textcolor'], kw['bg_boder_color'], kw['bg_radius'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.button_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        elif kw.get('button_radius',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s\n%s" % (kw['bcolor'],
                                     kw['tcolor'], kw['btn_bcolor'], kw['button_radius'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.button_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        elif kw.get('resettxtcolor',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s\n%s" % (kw['reset_bgcolor'],
                                     kw['resettxtcolor'], kw['resetborder'], kw['reset_radius'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.button_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()

        elif kw.get('border_color',False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s\n%s" % (kw['borderbgcolor'],
                                     kw['bordertexcolor'], kw['border_color'], kw['border_radius'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.button_create_attach_and_view(ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        return None

    def button_create_attach_and_view(self, ks_custom_url, datas, ks_scss_path):
        KsIrAttachment = request.env["ir.attachment"]
        _create_attach = {
            'name': ks_custom_url,
            'type': "binary",
            'mimetype': "text/scss",
            'datas': datas,
            'datas_fname': ks_scss_path.split("/")[-1],
            'url': ks_custom_url,
        }
        website = request.env['website'].get_current_website()
        _create_attach.update({
            'website_id': website.id,
        })
        KsIrAttachment.create(_create_attach)
        _KsIrUiView = request.env["ir.ui.view"]
        _ks_view_to_xpath = request.env['ir.ui.view'].search(
            [('key', '=', 'ks_theme_kinetik._ks_assets_primary_variables')], limit=1)

        create_view = {
            'name': ks_custom_url,
            'key': 'ks_theme_kinetik.scss_%s' % str(uuid.uuid4())[:6],
            'mode': "extension",
            'priority': 2,
            'inherit_id': _ks_view_to_xpath.id,
            'arch': """
                    <data inherit_id="%(inherit_xml_id)s" name="%(name)s">
                        <xpath expr="//link[@href='%(url_to_replace)s']" position="attributes">
                            <attribute name="href">%(new_url)s</attribute>
                        </xpath>
                    </data>
                """ % {
                'inherit_xml_id': _ks_view_to_xpath.xml_id,
                'name': ks_custom_url,
                'url_to_replace': '/' + 'ks_theme_kinetik' + ks_scss_path,
                'new_url': ks_custom_url,
            }
        }
        website = request.env['website'].get_current_website()
        create_view.update({
            'website_id': website.id,
        })
        _KsIrUiView.create(create_view)

    @http.route([
        '/write/updated/hoverscss',
    ], type='http', auth="public", website=True)
    def KsWriteUpdatedhoverScss(self, **kw):
        bundle_xmlid = 'web.assets_common'
        ks_scss_path = kw.get('scss_path', False)
        if kw.get('hovertextcolor', False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s" % (kw['hover_bgcolor'],
                                 kw['hovertextcolor'], kw['hover_border'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.hover_create_attach_and_view( ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        elif kw.get('hover_backgroundcolor', False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s" % (kw['hover_backgroundcolor'],
                                     kw['hovertcolor'], kw['hover_b_color'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.hover_create_attach_and_view( ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()

        elif kw.get('resethovertextcolor', False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s" % (kw['resethover_bgcolor'],
                                 kw['resethovertextcolor'], kw['resethover_border'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.hover_create_attach_and_view( ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()

        elif kw.get('hoverbordercolor', False):
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n%s\n%s" % (kw['hover_bg2color'],
                                 kw['hovertext2color'], kw['hoverbordercolor'] or "\n")).encode("utf-8"))
            if _ks_attachment:
                _ks_attachment.write({"datas": datas})
            else:
                self.hover_create_attach_and_view( ks_custom_url, datas, ks_scss_path)
            request.env["ir.qweb"].clear_caches()
        return None

    def hover_create_attach_and_view(self,ks_custom_url, datas , ks_scss_path):
        KsIrAttachment = request.env["ir.attachment"]
        _create_attach = {
            'name': ks_custom_url,
            'type': "binary",
            'mimetype': "text/scss",
            'datas': datas,
            'datas_fname': ks_scss_path.split("/")[-1],
            'url': ks_custom_url,
        }
        website = request.env['website'].get_current_website()
        _create_attach.update({
            'website_id': website.id,
        })
        KsIrAttachment.create(_create_attach)
        _KsIrUiView = request.env["ir.ui.view"]
        _ks_view_to_xpath = request.env['ir.ui.view'].search(
            [('key', '=', 'ks_theme_kinetik._ks_assets_primary_variables')], limit=1)

        create_view = {
            'name': ks_custom_url,
            'key': 'ks_theme_kinetik.scss_%s' % str(uuid.uuid4())[:6],
            'mode': "extension",
            'priority': 2,
            'inherit_id': _ks_view_to_xpath.id,
            'arch': """
                      <data inherit_id="%(inherit_xml_id)s" name="%(name)s">
                          <xpath expr="//link[@href='%(url_to_replace)s']" position="attributes">
                              <attribute name="href">%(new_url)s</attribute>
                          </xpath>
                      </data>
                  """ % {
                'inherit_xml_id': _ks_view_to_xpath.xml_id,
                'name': ks_custom_url,
                'url_to_replace': '/' + 'ks_theme_kinetik' + ks_scss_path,
                'new_url': ks_custom_url,
            }
        }
        website = request.env['website'].get_current_website()
        create_view.update({
            'website_id': website.id,
        })
        _KsIrUiView.create(create_view)

    @http.route([
        '/get/updated/scss',
    ], type='http', auth="public", website=True)
    def KsGetUpdatedScss(self, **kw):
        website = request.env['website'].get_current_website()
        view = request.env['ir.attachment'].search([
            ('name', '=', '/ks_theme_kinetik/static/src/css/ks_updated_color.custom.web.assets_common.scss'),
            ('website_id', '=', website.id)],limit=1)
        data = view['datas']
        if kw.get('scss_path', False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[0].split(":")[1][:8]
            return "#FAB446"
        elif kw.get('text_scss_path',False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[1].split(":")[1][:8]
            return "#FAB446"

    @http.route([
        '/get/updated/buttonscss',
    ], type='http', auth="public", website=True)
    def KsGetUpdatedbuttonScss(self, **kw):
        website = request.env['website'].get_current_website()
        view = request.env['ir.attachment'].search([
            ('name', '=', '/ks_theme_kinetik/static/src/css/ks_updated_button_color.custom.web.assets_common.scss'),
            ('website_id', '=', website.id)], limit=1)
        data = view['datas']
        if kw.get('bg_scss_path',False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[0].split(':')[1][:8]
            return "#FAB446"
        elif kw.get('text_scss_path',False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[1].split(':')[1][:8]
            return "#FAB446"
        elif kw.get('radius_scss_path',False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[3].split(':')[1].split('p')[0]
            return "0"
        elif kw.get('border_scss_path',False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[2].split(':')[1][:8]
            return "#FAB446"

    @http.route([
        '/get/updated/hoverscss',
    ], type='http', auth="public", website=True)
    def KsGetUpdatedhoverScss(self, **kw):
        website = request.env['website'].get_current_website()
        view = request.env['ir.attachment'].search([
            ('name', '=', '/ks_theme_kinetik/static/src/css/ks_updated_hover_color.custom.web.assets_common.scss'),
            ('website_id', '=', website.id)],limit=1)
        data = view['datas']
        if kw.get('hover_bg_scss_path', False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[0].split(':')[1][:8]
            return "#FAB446"
        elif kw.get('hover_text_scss_path', False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[1].split(':')[1][:8]
            return "#FAB446"
        elif kw.get('hover_border_scss_path', False):
            if data:
                theme_color = base64.b64decode(data).decode('utf-8')
                return theme_color.split('\n')[2].split(':')[1][:8]
            return "#FAB446"


    #controller for dynamic font url option
    @http.route(['/some_url'], type='json', auth="public", website=True)
    def dynamic_font(self, **kwargs):
        try:
            url = kwargs['url']

            font_family=url.split('=')[1].split(('&'))[0]
            if ':' in font_family:
                font_family=url.split('=')[1].split(('&'))[0].split(':')[0]
            count = max([int(i.key.split('_')[-1]) for i in request.env['ir.ui.view'].search([('key', 'like', 'ks_theme_kinetik.custom_font_layout_%'), ('active', 'in', [1,0])])])
            count += 1
            for i in list(punctuation):
                if i in font_family:
                    font_family = font_family.replace(i, ' ')
            data = "@import url(URLREPLACE);$ks-font-main:FONTREPLCER, sans-serif;body { font-family:$ks-font-main; }html *:not(.fa){font-family:$ks-font-main;}"
            if 'wght' in url:
                url = url.split(':')
                url = url[0] + ':' + url[1]
                if not '&display=swap' in url:
                    url = url + '&display=swap'
                else:
                    url = url
            else:
                url = url
            url = "'" + url + "'"
            data = data.replace('URLREPLACE', url)
            data = data.replace('FONTREPLCER', font_family)
            bundle_xmlid = 'web.assets_common'
            ks_scss_path = '/static/src/scss/fonts/default_'+str(count)+'.scss'
            ks_custom_url = self._ks_custom_scss_file_url(ks_scss_path, bundle_xmlid)
            ks_custom_url = '/' + 'ks_theme_kinetik' + ks_custom_url
            _ks_attachment = self._ks_get_attachment(ks_custom_url)
            datas = base64.b64encode(
                ("%s\n" % (data)).encode("utf-8"))
            if datas:
                self.font_create_attach_and_view(ks_custom_url, datas, ks_scss_path,font_family,count)
            request.env["ir.qweb"].clear_caches()

        except Exception as e:
            pass

    def font_create_attach_and_view(self, ks_custom_url, datas, ks_scss_path, font_family, count):
        KsIrAttachment = request.env["ir.attachment"]
        _create_attach = {
            'name': ks_custom_url,
            'type': "binary",
            'mimetype': "text/scss",
            'datas': datas,
            'datas_fname': ks_scss_path.split("/")[-1],
            'url': ks_custom_url,
        }
        website = request.env['website'].get_current_website()
        _create_attach.update({
            'website_id': website.id,
        })
        KsIrAttachment.create(_create_attach)
        _KsIrUiView = request.env["ir.ui.view"]
        assets = request.env['ir.ui.view'].search([('key', '=', 'web.assets_frontend')], limit=1)

        create_view = {
            'name': font_family,
            'key': 'ks_theme_kinetik.custom_font_layout_%s' % count,
            'mode': "extension",
            'priority': 8,
            'active': False,
            'inherit_id': assets.id,
            'arch': """
                      <data>
                          <xpath expr="." position="inside">
                             <link rel="stylesheet" type="text/scss" href="%(new_url)s"/>
                          </xpath>
                      </data>
                  """ % {
                'new_url': ks_custom_url,
            }
        }
        website = request.env['website'].get_current_website()
        create_view.update({
            'website_id': website.id,
        })
        _KsIrUiView.create(create_view)

    # handling event for deleting font
    @http.route(['/site'], type='json', auth="public", website=True)
    def delete_font(self, **kwargs):
        view_id = kwargs['view_id']
        if request.env['ir.ui.view'].browse(view_id):
            request.env['ir.ui.view'].browse(view_id).unlink()
        return

    @http.route(['/reset'], type='json', auth="public", website=True)
    def reset(self):
        module_path = '/'.join((os.path.realpath(__file__)).split('/')[:-2])
        path=module_path+'/static/src/css/ks_updated_button_color.scss'
        f=open(path,'r+')
        data=f.read()
        path1 = module_path + '/static/src/css/ks_updated_hover_color.scss'
        f1 = open(path1, 'r+')
        data1 = f1.read()
        values = {
            'bgcolor': data.split('\n')[1],
            'txtcolor': data.split('\n')[0],
            'radius': data.split('\n')[2],
            'border': data.split('\n')[3],
            'hoverbgcolor':data1.split('\n')[1],
            'hovertxtcolor':data1.split('\n')[0],
            'hoverbordercolor':data1.split('\n')[2]
        }
        return values

    @http.route(['/reset/themecolor'], type='json', auth="public", website=True)
    def reset_themecolor(self):
        module_path = '/'.join((os.path.realpath(__file__)).split('/')[:-2])
        path = module_path + '/static/src/css/ks_updated_color.scss'
        f = open(path, 'r+')
        data = f.read()
        value = {
            'themecolor': data.split('\n')[0],
            'themetxtcolor': data.split('\n')[1],
        }
        return value

    # Reset the Header
    @http.route(['/reset/header'], type='json', auth="public", website=True)
    def ks_reset_header(self):
        current_website = request.env['website'].get_current_website()
        delete_header_view = request.env['ir.ui.view'].search(['|', ('active', '!=', False), ('active', '=', False),
                                                           ('website_id', '=', current_website.id),
                                                           ('key', 'ilike', 'ks_theme_kinetik.custom_header_layout')])
        if delete_header_view:
            delete_header_view.unlink()
        key = 'ks_theme_kinetik.custom_header_layout%'
        request.cr.execute('update ir_ui_view set active = false where key LIKE %s', (key,))

    # Reset the Footers
    @http.route(['/reset/footer'], type='json', auth="public", website=True)
    def ks_reset_footer(self):
        current_website = request.env['website'].get_current_website()
        delete_footer_view = request.env['ir.ui.view'].search(['|', ('active', '!=', False), ('active', '=', False),
                                                           ('website_id', '=', current_website.id),
                                                           ('key', 'ilike', 'ks_theme_kinetik.custom_footer_layout')])
        if delete_footer_view:
            delete_footer_view.unlink()
        key = 'ks_theme_kinetik.custom_footer_layout%'
        request.cr.execute('update ir_ui_view set active = false where key LIKE %s', (key,))


