-- ========================================================================
-- Script para limpiar reglas y grupos viejos de account_invoice_line_report
-- Ejecutar ANTES de actualizar el módulo
-- ========================================================================

BEGIN;

-- 1. Eliminar reglas ir.rule que ya no se usan
DELETE FROM ir_rule 
WHERE id IN (
    SELECT res_id FROM ir_model_data 
    WHERE module = 'account_invoice_line_report' 
    AND name IN (
        'crm_team_multicompany_read_rule',
        'crm_team_accounting_all_read_rule',
        'crm_team_export_historical_invoices_rule'
    )
);

-- 2. Eliminar grupos que ya no se usan
DELETE FROM res_groups 
WHERE id IN (
    SELECT res_id FROM ir_model_data 
    WHERE module = 'account_invoice_line_report' 
    AND name IN (
        'group_crm_team_multi_company_read',
        'group_export_historical_invoices'
    )
);

-- 3. Eliminar referencias en ir_model_data
DELETE FROM ir_model_data 
WHERE module = 'account_invoice_line_report' 
AND name IN (
    'crm_team_multicompany_read_rule',
    'crm_team_accounting_all_read_rule',
    'crm_team_export_historical_invoices_rule',
    'group_crm_team_multi_company_read',
    'group_export_historical_invoices'
);

-- 4. Verificar que se eliminaron
SELECT 'Reglas restantes:' as tipo, COUNT(*) as cantidad
FROM ir_rule r
JOIN ir_model_data imd ON imd.res_id = r.id AND imd.model = 'ir.rule'
WHERE imd.module = 'account_invoice_line_report'
UNION ALL
SELECT 'Grupos restantes:', COUNT(*)
FROM res_groups g
JOIN ir_model_data imd ON imd.res_id = g.id AND imd.model = 'res.groups'
WHERE imd.module = 'account_invoice_line_report';

-- Si todo se ve bien, hacer COMMIT. Si no, hacer ROLLBACK.
-- COMMIT;
-- ROLLBACK;

