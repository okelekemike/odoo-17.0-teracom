
from odoo import models, fields, _
from odoo.tools import float_compare,float_is_zero

class PosSession(models.Model):
    _inherit = "pos.session"

    def _validate_session(self, balancing_account=False, amount_to_balance=0, bank_payment_method_diffs=None):
        vals = super(PosSession, self)._validate_session()

        all_related_moves = self._get_related_account_moves()
        all_move_lines = self.env['account.move.line'].sudo().search([
                                    ('id','in',all_related_moves.mapped('line_ids').ids),
                                    ('name','in',[
                                        'Cash difference observed during the counting (Loss)',
                                        'Cash difference observed during the counting (Profit)',
                                        'Cash difference observed during the counting (Loss) - opening',
                                        'Cash difference observed during the counting (Loss) - closing',
                                        'Cash difference observed during the counting (Profit) - opening',
                                        'Cash difference observed during the counting (Profit) - closing',
                                    ]),
                            ])
        unique_move_ids = set(all_move_lines.mapped('move_id'))
        # Filter the all_move_lines based on unique move_ids
        filtered_move_lines = all_move_lines.filtered(lambda line: line.move_id in unique_move_ids)

        for each in filtered_move_lines:
            each.move_id.button_draft()
            each.move_id.sudo().write({
                'ref': self.name + " - " + self.config_id.name,
            }) 
            each.move_id.button_cancel()


        return True

    def _loader_params_product_product(self):
        result = super()._loader_params_product_product()
        result["search_params"]["fields"].append("available_lot_for_pos_ids")
        return result

    def get_pos_ui_product_product_by_params(self, custom_search_params):
        return super(
            PosSession, self.with_company(self.company_id.id)
        ).get_pos_ui_product_product_by_params(custom_search_params)