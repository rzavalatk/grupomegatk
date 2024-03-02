from odoo import models, fields, api

class CustomAccountMove(models.Model):
    _inherit = 'account.move'
    
    #SE COMENTO 'PORQUE EN LA NUEVA VERSION YA NO FUNCIONA DE LA MISMA FORMA
    """@api.model_create_multi
    def write(self, vals):
        for move in self:
            if 'line_ids' in vals:
                # Comenta o elimina el bloque de código que deseas desactivar
                # if self._context.get('check_move_validity', False):
                #     move._check_balanced()
                move.update_lines_tax_exigibility()
        return super(CustomAccountMove, self).write(vals)"""
    
    """def _check_balanced(self):
        #Assert the move is fully balanced debit = credit.
        #An error is raised if it's not the case.
        
        moves = self.filtered(lambda move: move.line_ids)
        if not moves:
            return

        # /!\ As this method is called in create / write, we can't make the assumption the computed stored fields
        # are already done. Then, this query MUST NOT depend on computed stored fields (e.g. balance).
        # It happens as the ORM makes the create with the 'no_recompute' statement.
        self.env['account.move.line'].flush(self.env['account.move.line']._fields)
        s+-+elf.env['account.move'].flush(['journal_id'])
        self._cr.execute('''
            SELECT line.move_id, ROUND(SUM(line.debit - line.credit), currency.decimal_places)
            FROM account_move_line line
            JOIN account_move move ON move.id = line.move_id
            JOIN account_journal journal ON journal.id = move.journal_id
            JOIN res_company company ON company.id = journal.company_id
            JOIN res_currency currency ON currency.id = company.currency_id
            WHERE line.move_id IN %s
            GROUP BY line.move_id, currency.decimal_places
            HAVING ROUND(SUM(line.debit - line.credit), currency.decimal_places) != 0.0;
        ''', [self.ids])

        query_res = self._cr.fetchall()
        if query_res:
            ids = [res[0] for res in query_res]
            sums = [res[1] for res in query_res]
            # Comenta la siguiente línea para desactivar la excepción
            # raise UserError(_("Cannot create unbalanced journal entry. Ids: %s\nDifferences debit - credit: %s") % (ids, sums))
"""
