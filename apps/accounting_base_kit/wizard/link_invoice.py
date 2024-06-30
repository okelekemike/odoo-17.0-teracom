# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LinkInvoice(models.TransientModel):
    """
    This model handles the linking of invoices to sale orders.
    """
    _name = 'link.invoice'
    _description = "Link Invoice"

    invoice_ids = fields.Many2many(
        'account.move', string='Invoices',
        help="Select the invoices you want to link to the sale order.")
    sale_order_id = fields.Many2one(
        'sale.order', string='Default Sale Order', readonly=True,
        help="The default sale order to which the selected invoices will be linked.")

    def action_add_invoices(self):
        """
        Add selected invoices to the associated sale order and perform
        validation checks.
        """
        if self.sale_order_id:
            for invoice in self.invoice_ids:
                if invoice.link_invoice:
                    matched_products = self.sale_order_id.order_line.mapped('product_id')
                    for invoice_line in invoice.invoice_line_ids.product_id:
                        if invoice_line not in matched_products:
                            raise ValidationError(_(
                                "Invoice contains a product not present in the Sale "
                                "Order: %s" % invoice_line.display_name))
                        for line in self.sale_order_id.order_line.filtered(
                                lambda x: x.product_id == invoice_line):
                            delivery_quantity = line.product_uom_qty
                            line.qty_invoiced = delivery_quantity
                            line.invoice_lines |= invoice.invoice_line_ids.filtered(
                                lambda x: x.product_id == line.product_id)

    @api.constrains('invoice_ids')
    def invoice_ids_field(self):
        """
        Check for partner mismatch between sale order and selected invoices.
        """
        for invoice in self:
            sale_order_partner_id = invoice.sale_order_id.partner_id
            for inv_line in invoice.invoice_ids:
                if inv_line.partner_id != sale_order_partner_id:
                    raise ValidationError(_(
                        "Partner mismatch between Sale Order and Invoice. "
                        "Please remove it to Link Invoice"))
