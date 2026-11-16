# Sentinel invoice audit — Odoo 18

Company scope is fixed to MEGATK (8) and MEDITEK (9), intersected with the reader's native Odoo company permissions. This addon adds an append-only event store and a pure-read invoice chatter projection. It grants no accounting write, posting, approval, cancellation, reconciliation, user-management or Settings permissions.

The audit reader role also rejects financial `create/write/unlink` on the five captured models, even if other pre-existing groups grant writes. This is necessary because Odoo ACL grants are additive. No request context or internal `sudo` retaining that auditor identity bypasses the guard. Other users' permissions and the auditor's existing groups are not removed or rewritten; only the dedicated role's members receive this financial read-only restriction. Permissions on unrelated Odoo models are outside this addon.

## Evidence and limits

`sentinel.invoice.audit.event` records the effective ORM user before the logger's internal storage elevation. UUIDs identify events; `source_event_uid` deduplicates the same operation projected against several invoices. `correlation_uid` links nested ORM operations. UTC microsecond ISO timestamps supplement Odoo's timestamp field. Company, invoice/payment/ledger identifiers and safe stored old/new values are snapshots, not foreign keys to objects that may later be removed. A posted event snapshots payment terms, their definition and due lines at that operation. It does not infer historic terms from the current invoice.

`account.partial.reconcile.unlink` copies both lines, invoice, originating payment, currency and applied amounts before deletion, appending in the same database transaction after successful deletion. Creation and deletion remain separate immutable events. A later create involving the same endpoints proves a later application; it does not by itself prove that an operator intended to undo the earlier removal. Full-reconcile events are noncanonical for amount totals: count partial events once.

HTTP/API evidence never implies a human clicked a button. Native cron and base-automation entrypoints carry server-side provenance that cannot be supplied through RPC context. Other execution paths remain unclassified. Effective user and initiating user are separate where the entrypoint provides them. Business methods retain their existing permissions; only audit insertion uses `sudo`.

`sentinel.invoice.audit.message` exposes existing invoice messages and native tracking values subject to invoice/company/message access and field visibility. It calls no mail controller that marks notifications read. Native message creator/author are evidence, not a guaranteed reconstruction of an executor. Removed or restricted fields are withheld. Binary, group-restricted, secret-like and non-stored fields are excluded from new event values; long texts disclose truncation. Raw SQL changes bypass ORM capture and are outside the guarantee. Database administrators can change the database directly; this is not a tamper-proof external ledger.

## Historical coverage

`sentinel.invoice.audit.coverage` stores the actual installation start, once per company, without backdating. No pre-install history is fabricated. Native chatter and older Auditlog rows may recover partial history before that timestamp; they cannot establish completeness or exclude changes later reverted. The interval from 2026-11-01 to the real capture start must remain explicitly marked as unproven. The addon does not subscribe or rewrite existing Auditlog rules or delete existing history.

## Access and deployment

1. Run the included Odoo 18 CI against a new synthetic PostgreSQL database. Test posting, cancellation/reset, rollback, removal and reapplication, company isolation and denied writes.
2. Back up the Odoo.sh database and filestore. Deploy the feature commit to a staging branch cloned from current production. Install this addon using Luis Morán's authorized administrative session, never Jennifer's session or an unapproved superuser elevation.
3. Verify installation, exact company scope, message visibility, UTC start markers and compatibility with installed custom accounting/SAR addons. Do not create real financial documents or consume fiscal numbers to test production.
4. On installation, only the existing exact auditor `analisis.codex@megatk.com` (UID 533) is given the new **read-only** audit group. No other existing groups or companies are changed. System administrators can inspect the projections through a read-only ACL. Review any additional group assignment explicitly.
5. Deploy the corresponding Sentinel reader only after confirming the addon is available. Keep credential encryption, stored connections and company policies unchanged. The connector must use only search_read/search_count/fields_get with fixed projections.
6. Install in production only after staging tests pass and report the real start timestamp. Keep the previous CAI, fiscal sequences and other modules unchanged.

## Rollback

Restore code to the tested compatible release while retaining the addon and its event tables. Do **not uninstall** this addon as a routine rollback: uninstalling removes audit history. A full database restore also rolls back business transactions and audit events since the backup and therefore requires a separate maintenance decision. Existing immutable coverage markers must never be reset to conceal a gap.
