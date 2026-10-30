"""Verify the installed ir.http hook without making external HTTP requests."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    from odoo.tests.common import TransactionCase
except ModuleNotFoundError:
    TransactionCase = None

if TransactionCase is not None:
    from werkzeug.routing import RequestRedirect
    from . import ir_http

    class TestHttpsRouting(TransactionCase):
        def test_installed_hook_redirects_before_dispatch(self):
            fake = SimpleNamespace(httprequest=SimpleNamespace(
                url='http://www.megatk.net/shop?search=impresora&x=1&x=2',
            ))
            with patch.object(ir_http, 'request', fake):
                with self.assertRaises(RequestRedirect) as caught:
                    self.env['ir.http']._match('/shop')
            response = caught.exception.get_response()
            self.assertEqual(response.status_code, 308)
            self.assertEqual(response.headers['Location'],
                             'https://www.megatk.net/shop?search=impresora&x=1&x=2')

        def test_unknown_path_redirects_before_matching(self):
            fake = SimpleNamespace(httprequest=SimpleNamespace(
                url='http://www.megatk.net/not-an-existing-page?x=1',
            ))
            with patch.object(ir_http, 'request', fake):
                with self.assertRaises(RequestRedirect) as caught:
                    self.env['ir.http']._match('/not-an-existing-page')
            self.assertEqual(caught.exception.new_url,
                             'https://www.megatk.net/not-an-existing-page?x=1')
