from odoo.tests import HttpCase, tagged
from odoo.addons.web.tests.test_js import unit_test_error_checker


@tagged('post_install', '-at_install')
class TestLenkaFinancialValidationUI(HttpCase):
    def test_field_guidance_in_browser(self):
        # HOOT identifies suites by the JS module's canonical name.
        name = '@lenka_financiero/financial_validation'
        hash_value = 0
        for char in name:
            hash_value = ((hash_value << 5) - hash_value + ord(char)) & 0xFFFFFFFF
        self.browser_js(
            '/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&id=%08x' % hash_value,
            '', '', login='admin', timeout=240,
            success_signal='[HOOT] Test suite succeeded', error_checker=unit_test_error_checker,
        )
