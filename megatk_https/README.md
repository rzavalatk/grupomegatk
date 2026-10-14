# MEGATK HTTPS

Small Odoo 18 add-on scoped to `www.megatk.net` and `megatk.net` only.
Install after deploying the code. The existing TLS certificate remains managed
by Odoo.sh. No DNS, mail, permissions or accounting data changes are included.

HTTP page requests redirect with status 308 to `https://www.megatk.net`, keeping
the path and query string. HTTPS and all other company domains are unchanged.
The ACME challenge path is excluded to preserve certificate validation.
The scheme comes from Odoo/Werkzeug after the platform's trusted proxy handling.

Validation: `python -m unittest discover -s megatk_https -v`, then verify a live
HTTP request redirects once and HTTPS responds successfully. Check `/shop` and
a query string as well as the homepage.

Rollback: uninstall only this add-on or revert its deployment, then verify the
website. The module stores no business data and changes no existing records.
