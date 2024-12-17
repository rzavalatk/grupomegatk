# -*- coding: utf-8 -*-

import json
import logging
from odoo import http
from odoo.http import request
from datetime import date

_logger = logging.getLogger(__name__)


class RestApi(http.Controller):
    """Este es un controlador que se utiliza para generar respuestas basadas en las solicitudes api"""

    def auth_api_key(self, api_key):
        """Esta función se utiliza para autenticar la api-key al enviar una solicitud"""
        
        
        logging.warning(api_key)
        user_id = request.env['res.users'].search([('api_key', '=', api_key)])
        if api_key is not None and user_id:
            response = True
        elif not user_id:
            response = ('<html><body><h2>Invalid <i>API Key</i> '
                        '!</h2></body></html>')
        else:
            response = ("<html><body><h2>No <i>API Key</i> Provided "
                        "!</h2></body></html>")

        return response

    def generate_response(self, method, model, rec_id):
        """Esta función se utiliza para generar la respuesta en función del tipo de solicitud y de los parámetros dados"""
        option = request.env['connection.api'].search(
            [('model_id', '=', model)], limit=1)
        model_name = option.model_id.model

        if method != 'DELETE':
            data = json.loads(request.httprequest.data)
        else:
            data = {}
        fields = []
        if data:
            for field in data['fields']:
                fields.append(field)
        if not fields and method != 'DELETE':
            return ("<html><body><h2>No hay campos seleccionados para el modelo"
                    "</h2></body></html>")
        if not option:
            return ("<html><body><h2>No se ha creado ningún registro para el modelo"
                    "</h2></body></html>")
        try:
            if method == 'GET':
                fields = []
                
                for field in data['fields']:
                    fields.append(field)
                
                if not option.is_get:
                    return ("<html><body><h2>Método no permitido"
                            "</h2></body></html>")
                else:
                    datas = []
                    if rec_id != 0:
                        try:
                            partner_records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', rec_id)],
                                fields=fields
                            )

                            for record in partner_records:
                                    for key, value in record.items():
                                        if isinstance(value, date):
                                            record[key] = value.strftime('%Y-%m-%d')

                            data = json.dumps({
                                'records': partner_records
                            })
                            datas.append(data)
                            return request.make_response(data=datas)
                        except Exception as e:
                            logging.error("Error during JSON serialization: " + str(e))
                            return ("<html><body><h2>Internal Server Error, verificar logs</h2></body></html>")
                    else:
                        try:
                            partner_records = request.env[model_name].search_read(domain=[], fields=fields)
                            
                            for record in partner_records:
                                for key, value in record.items():
                                    if isinstance(value, date):
                                        record[key] = value.strftime('%Y-%m-%d')

                            # Prueba si esto lanza un error
                            data = json.dumps({
                                'records': partner_records
                            })
                            
                            return request.make_response(data)
                        except Exception as e:
                            logging.error("Error during JSON serialization: " + str(e))
                            return ("<html><body><h2>Internal Server Error, verificar logs</h2></body></html>")
        except:
            return ("<html><body><h2>Invalid JSON Data"
                    "</h2></body></html>")
        if method == 'POST':
            if not option.is_post:
                return ("<html><body><h2>Método no permitido"
                        "</h2></body></html>")
            else:
                logging.warning("POST")
                try:
                    try:
                        data = json.loads(request.httprequest.data)
                        datas = []
                        new_resource = request.env[model_name].create(
                            data['values'])
                        partner_records = request.env[
                            model_name].search_read(
                            domain=[('id', '=', new_resource.id)],
                            fields=fields
                        )
                        for record in partner_records:
                                for key, value in record.items():
                                    if isinstance(value, date):
                                        record[key] = value.strftime('%Y-%m-%d')

                        new_data = json.dumps({'New resource': partner_records, })
                        datas.append(new_data)
                        return request.make_response(data=datas)
                    except Exception as e:
                        logging.error("Error during JSON serialization POST: " + str(e))
                        return ("<html><body><h2>Internal Server Error, verificar logs</h2></body></html>")
                except:
                    return ("<html><body><h2>Invalid JSON Data"
                            "</h2></body></html>")
        if method == 'PUT':
            if not option.is_put:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:
                        try:
                            datas = []
                            data = json.loads(request.httprequest.data)
                            resource.write(data['values'])
                            partner_records = request.env[
                                str(model_name)].search_read(
                                domain=[('id', '=', resource.id)],
                                fields=fields
                            )
                            new_data = json.dumps(
                                {'Updated resource': partner_records,
                                 })
                            datas.append(new_data)
                            return request.make_response(data=datas)

                        except:
                            return ("<html><body><h2>Invalid JSON Data "
                                    "!</h2></body></html>")
        if method == 'DELETE':
            if not option.is_delete:
                return ("<html><body><h2>Method Not Allowed"
                        "</h2></body></html>")
            else:
                if rec_id == 0:
                    return ("<html><body><h2>No ID Provided"
                            "</h2></body></html>")
                else:
                    resource = request.env[str(model_name)].browse(
                        int(rec_id))
                    if not resource.exists():
                        return ("<html><body><h2>Resource not found"
                                "</h2></body></html>")
                    else:

                        records = request.env[
                            str(model_name)].search_read(
                            domain=[('id', '=', resource.id)],
                            fields=['id', 'display_name']
                        )
                        remove = json.dumps(
                            {"Resource deleted": records,
                             })
                        resource.unlink()
                        return request.make_response(data=remove)

    @http.route(['/send_request'], type='http',
                auth='none',
                methods=['GET', 'POST', 'PUT', 'DELETE'], csrf=False)
    def fetch_data(self, **kw):
        """Este controlador será llamado cuando se envíe una petición a la url especificada, y autenticará la api-key y luego generará el resultado"""

        http_method = request.httprequest.method
        api_key = request.httprequest.headers.get('api-key')
        auth_api = self.auth_api_key(api_key)
        model = kw.get('model')
        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        request.session.authenticate(request.session.db, username,
                                     password)
        model_id = request.env['ir.model'].search(
            [('model', '=', model)])
        if not model_id:
            return ("<html><body><h3>Invalid model, check spelling or maybe "
                    "the related "
                    "module is not installed"
                    "</h3></body></html>")

        if auth_api == True:
            if not kw.get('Id'):
                rec_id = 0
            else:
                rec_id = int(kw.get('Id'))
            result = self.generate_response(http_method, model_id.id, rec_id)
            return result
        else:
            return auth_api

    @http.route(['/odoo_connect'], type="http", auth="none", csrf=False,
                methods=['GET'])
    def odoo_connect(self, **kw):
        """Este es el controlador que inicializa la transacción api generando la clave api para un usuario y base de datos específicos."""

        username = request.httprequest.headers.get('login')
        password = request.httprequest.headers.get('password')
        db = request.httprequest.headers.get('db')
        try:
            request.session.update(http.get_default_session(), db=db)
            auth = request.session.authenticate(request.session.db, username,
                                                password)
            user = request.env['res.users'].browse(auth)
            api_key = request.env.user.generate_api(username)
            datas = json.dumps({"Status": "auth successful",
                                "User": user.name,
                                "api-key": api_key})
            return request.make_response(data=datas)
        except:
            return ("<html><body><h2>wrong login credentials"
                    "</h2></body></html>")
