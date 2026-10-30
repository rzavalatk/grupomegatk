from werkzeug.routing import RequestRedirect

from odoo import models
from odoo.http import request

from .redirect import https_target


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _match(cls, path_info):
        target = https_target(request.httprequest.url)
        if target:
            # 308 preserves request method, path and query. Raise before route
            # authentication or dispatch, including for unknown page paths.
            raise RequestRedirect(target)
        return super()._match(path_info)
