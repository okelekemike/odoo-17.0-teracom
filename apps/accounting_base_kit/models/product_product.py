# -*- coding: utf-8 -*-

import math
from odoo import fields, api, models
from odoo.tools import float_compare


def ean_checksum(eancode):
    """Returns the checksum of an ean string of length 13, returns -1 if
    the string has the wrong length"""
    if len(eancode) != 13:
        return -1
    odd_sum = 0
    even_sum = 0
    for rec in range(len(eancode[::-1][1:])):
        if rec % 2 == 0:
            odd_sum += int(eancode[::-1][1:][rec])
        else:
            even_sum += int(eancode[::-1][1:][rec])
    total = (odd_sum * 3) + even_sum
    return int(10 - math.ceil(total % 10.0)) % 10


def check_ean(eancode):
    """Returns True if ean code is a valid ean13 string, or null"""
    if not eancode:
        return True
    if len(eancode) != 13:
        return False
    try:
        int(eancode)
    except:
        return False
    return ean_checksum(eancode)


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    product_identifier = '00000000000' + ean
    ean = product_identifier[-11:]
    check_number = check_ean(ean + '00')
    return f'{ean}0{check_number}'


class ProductProduct(models.Model):
    """Inherit product_product model for adding EAN13 Standard Barcode"""
    _inherit = 'product.product'

    def generate_ref(self, rec):
        product_name_config = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.product_name_config')
        pro_name_digit = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_name_digit')
        pro_name_separator = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_name_separator')
        pro_categ_config = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_categ_config')
        pro_categ_digit = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_categ_digit')
        pro_categ_separator = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_categ_separator')
        pro_template_config = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_template_config')
        pro_template_digit = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_template_digit')
        pro_template_separator = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.pro_template_separator')
        default_code = ""
        if rec.detailed_type == 'consu':
            default_code += 'CON:'
        elif rec.detailed_type == 'service':
            default_code += 'SER:'
        elif rec.detailed_type == 'product':
            default_code += 'STO:'
        if product_name_config:
            default_code += rec.name[:int(pro_name_digit)]
            default_code += pro_name_separator
        if pro_categ_config:
            default_code += rec.categ_id.name[:int(pro_categ_digit)]
            default_code += pro_categ_separator
        if pro_template_config:
            for attribute in rec.attribute_line_ids:
                for value in attribute.value_ids:
                    default_code += value.name[:int(pro_template_digit)]
                    default_code += pro_template_separator
        sequence_code = 'attribute.sequence.ref'
        default_code += self.env['ir.sequence'].next_by_code(sequence_code)
        return default_code.upper()

    @api.model_create_multi
    def create(self, vals_list):
        """Function to add EAN13 Standard barcode at the time
        create new product"""
        res = super(ProductProduct, self).create(vals_list)

        auto_generate_barcode = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.auto_generate_barcode')
        if auto_generate_barcode:
            for vals in res:
                if vals.barcode:
                    continue
                ean = generate_ean(str(vals.id))
                vals.barcode = '21' + ean[2:]

        # supering the create function, generating the internal reference
        auto_generate_internal_ref = self.env['ir.config_parameter'].sudo().get_param(
            'accounting_base_kit.auto_generate_internal_ref')
        if auto_generate_internal_ref:
            for rec in res:
                if rec.default_code:
                    continue
                rec.default_code = self.generate_ref(rec)
        return res

    @api.model
    def action_generate_internal_ref_pro(self):
        """creating the internal reference"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.product'].browse(active_ids)
        for rec in products:
            rec.default_code = self.generate_ref(rec)
        return self

    po_product_line_ids = fields.One2many('purchase.product.history.line',
                                          'product_history_id',
                                          string='Purchase History',
                                          compute='_compute_po_product_line_ids',
                                          help='Purchased product variant details')

    def _compute_po_product_line_ids(self):
        """Compute the purchase history lines. It will show all purchase order
         details of the particular product in product.template based on the
          limit and status."""
        self.po_product_line_ids = False
        status = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.po_status')
        limit = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.po_limit')
        if int(limit) >= 0 and status:
            if status == 'all':
                state = ('draft', 'sent', 'to approve', 'purchase', 'done', 'cancel')
            elif status == 'rfq':
                state = 'draft'
            elif status == 'purchase_order':
                state = ('purchase', 'done')
            elif status == 'in_process':
                state = ('sent', 'to approve')
            else:
                state = ''
            po_order_line = self.env['purchase.order.line'].search([
                ('product_id', '=', self.id), ('state', 'in', state)
            ], limit=(None if limit == 0 else limit))

            self.env['purchase.product.history.line'].create([{
                'product_history_id': self.id,
                'order_date': line.order_id.date_order,
                'order_reference_id': line.order_id.id,
                'description': line.name,
                'price_unit': line.price_unit,
                'product_qty': line.product_qty,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
            } for line in po_order_line])

    so_product_line_ids = fields.One2many('sale.product.history.line',
                                          'product_history_id',
                                          string='Sale History',
                                          compute='_compute_so_product_line_ids',
                                          help='Sale product variant details')

    def _compute_so_product_line_ids(self):
        """Compute the sale history lines. It will show all sale order
         details of the particular product in product.template based on the
          limit and status."""
        self.so_product_line_ids = False
        status = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.so_status')
        limit = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.so_limit')
        if int(limit) >= 0 and status:
            if status == 'all':
                state = ('draft', 'sent', 'to approve', 'sale', 'done', 'cancel')
            elif status == 'rfq':
                state = 'draft'
            elif status == 'sale_order':
                state = ('sale', 'done')
            elif status == 'in_process':
                state = ('sent', 'to approve')
            else:
                state = ''
            so_order_line = self.env['sale.order.line'].search([
                ('product_id', '=', self.id), ('state', 'in', state)
            ], limit=(None if limit == 0 else limit))
            self.env['sale.product.history.line'].create([{
                'product_history_id': self.id,
                'order_date': line.order_id.date_order,
                'order_reference_id': line.order_id.id,
                'description': line.product_id.name,
                'price_unit': line.price_unit,
                'product_qty': line.product_uom_qty,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
            } for line in so_order_line])

    pos_product_line_ids = fields.One2many('pos.product.history.line',
                                           'product_history_id',
                                           string='Point Of Sale History',
                                           compute='_compute_pos_product_line_ids',
                                           help='Point Of Sale product variant details')

    def _compute_pos_product_line_ids(self):
        """Compute the point of sale history lines. It will show all pos order
         details of the particular product in product.template based on the
          limit and status"""
        self.pos_product_line_ids = False
        limit = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.so_limit')
        if int(limit) >= 0:
            pos_order_line = self.env['pos.order.line'].search([
                ('product_id', '=', self.id)
            ], limit=(None if limit == 0 else limit))
            self.env['pos.product.history.line'].create([{
                'product_history_id': self.id,
                'order_date': line.order_id.date_order,
                'order_reference_id': line.order_id.id,
                'description': line.product_id.name,
                'price_unit': line.price_unit,
                'product_qty': line.qty,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_subtotal_incl,
                } for line in pos_order_line])

    def action_published_product(self):
        return self.env['product.template'].action_published_product(self)

    def action_unpublished_product(self):
        return self.env['product.template'].action_unpublished_product(self)

    available_lot_for_pos_ids = fields.Json(
        compute="_compute_available_lot_for_pos", prefetch=False
    )

    @api.depends()
    @api.depends_context("company")
    def _compute_available_lot_for_pos(self):
        for record in self:
            record.available_lot_for_pos_ids = record.get_available_lots_for_pos(
                self.env.company.id
            )

    def get_available_lots_for_pos(self, company_id):
        self.ensure_one()
        if self.type != "product" or self.tracking == "none":
            return []
        lots = (
            self.env["stock.lot"]
                .sudo()
                .search(
                [
                    "&",
                    ["product_id", "=", self.id],
                    "|",
                    ["company_id", "=", company_id],
                    ["company_id", "=", False],
                ]
            )
        )

        lots = lots.filtered(
            lambda lot: float_compare(
                lot.product_qty, 0, precision_digits=lot.product_uom_id.rounding
            )
                        > 0
        )
        return [lot._get_pos_info() for lot in lots]
