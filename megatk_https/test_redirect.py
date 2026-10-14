"""Run without Odoo: python -m unittest discover -s megatk_https."""

import importlib.util
from pathlib import Path
import unittest

try:
    from odoo.tests.common import BaseCase
except ModuleNotFoundError:
    BaseCase = unittest.TestCase

spec = importlib.util.spec_from_file_location(
    'megatk_https_policy', Path(__file__).with_name('redirect.py'),
)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class TestHttpsPolicy(BaseCase):
    def test_public_http_home(self):
        self.assertEqual(policy.https_target('http://www.megatk.net/'),
                         'https://www.megatk.net/')

    def test_path_and_query_preserved(self):
        self.assertEqual(
            policy.https_target('http://www.megatk.net/shop/a%20b?x=1&x=2&next=%2Fshop'),
            'https://www.megatk.net/shop/a%20b?x=1&x=2&next=%2Fshop',
        )

    def test_apex_uses_canonical_host(self):
        self.assertEqual(policy.https_target('http://megatk.net/shop'),
                         'https://www.megatk.net/shop')

    def test_https_has_no_loop(self):
        self.assertIsNone(policy.https_target('https://www.megatk.net/shop'))

    def test_other_companies_and_odoo_unchanged(self):
        for host in ['www.meditekhn.net', 'www.klamusa.com', 'grupomegatk.odoo.com']:
            with self.subTest(host=host):
                self.assertIsNone(policy.https_target('http://' + host + '/'))

    def test_host_suffix_and_query_cannot_choose_destination(self):
        self.assertIsNone(policy.https_target('http://www.megatk.net.attacker.invalid/'))
        self.assertEqual(
            policy.https_target('http://www.megatk.net/?next=https://other.invalid'),
            'https://www.megatk.net/?next=https://other.invalid',
        )

    def test_certificate_validation_not_redirected(self):
        self.assertIsNone(policy.https_target(
            'http://www.megatk.net/.well-known/acme-challenge/token'))

    def test_explicit_http_port_is_removed(self):
        self.assertEqual(policy.https_target('http://www.megatk.net:80/shop'),
                         'https://www.megatk.net/shop')


if __name__ == '__main__':
    unittest.main()
