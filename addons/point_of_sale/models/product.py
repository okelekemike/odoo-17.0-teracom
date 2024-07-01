# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from itertools import groupby
from operator import itemgetter
from datetime import date


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    available_in_pos = fields.Boolean(string='Available in POS', help='Check if you want this product to appear in the Point of Sale.', default=False)
    to_weight = fields.Boolean(string='To Weigh With Scale', help="Check if the product should be weighted using the hardware scale integration.")
    pos_categ_ids = fields.Many2many(
        'pos.category', string='Point of Sale Category',
        help="Category used in the Point of Sale.")
    combo_ids = fields.Many2many('pos.combo', string='Combinations')
    detailed_type = fields.Selection(selection_add=[
        ('combo', 'Combo')
    ], ondelete={'combo': 'set consu'})
    type = fields.Selection(selection_add=[
        ('combo', 'Combo')
    ], ondelete={'combo': 'set consu'})

    @api.ondelete(at_uninstall=False)
    def _unlink_except_open_session(self):
        product_ctx = dict(self.env.context or {}, active_test=False)
        if self.with_context(product_ctx).search_count([('id', 'in', self.ids), ('available_in_pos', '=', True)]):
            if self.env['pos.session'].sudo().search_count([('state', '!=', 'closed')]):
                raise UserError(_("To delete a product, make sure all point of sale sessions are closed.\n\n"
                    "Deleting a product available in a session would be like attempting to snatch a"
                    "hamburger from a customer’s hand mid-bite; chaos will ensue as ketchup and mayo go flying everywhere!"))

    @api.onchange('sale_ok')
    def _onchange_sale_ok(self):
        if not self.sale_ok:
            self.available_in_pos = False

    @api.constrains('available_in_pos')
    def _check_combo_inclusions(self):
        for product in self:
            if not product.available_in_pos:
                combo_name = self.env['pos.combo.line'].sudo().search([('product_id', 'in', product.product_variant_ids.ids)], limit=1).combo_id.name
                if combo_name:
                    raise UserError(_('You must first remove this product from the %s combo', combo_name))

    def _create_variant_ids(self):
        res = super()._create_variant_ids()
        for template in self:
            archived_product = self.env['product.product'].search([('product_tmpl_id', '=', template.id), ('active', '=', False)], limit=1)
            if archived_product:
                combo_choices_to_delete = self.env['pos.combo.line'].search([
                    ('product_id', '=', archived_product.id)
                ])
                if combo_choices_to_delete:
                    # Delete old combo line
                    combo_ids = combo_choices_to_delete.mapped('combo_id')
                    combo_choices_to_delete.unlink()
                    # Create new combo line (one for each new variant) in each combo
                    new_variants = template.product_variant_ids.filtered(lambda v: v.active)
                    self.env['pos.combo.line'].create([
                        {
                            'product_id': variant.id,
                            'combo_id': combo_id.id,
                        }
                        for variant in new_variants for combo_id in combo_ids
                    ])
        return res

    @api.onchange('type')
    def _onchange_type(self):
        if self.type == "combo" and self.attribute_line_ids:
            raise UserError(_("Combo products cannot contains variants or attributes"))
        return super()._onchange_type()

class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.ondelete(at_uninstall=False)
    def _unlink_except_active_pos_session(self):
        product_ctx = dict(self.env.context or {}, active_test=False)
        if self.env['pos.session'].sudo().search_count([('state', '!=', 'closed')]):
            if self.with_context(product_ctx).search_count([('id', 'in', self.ids), ('product_tmpl_id.available_in_pos', '=', True)]):
                raise UserError(_("To delete a product, make sure all point of sale sessions are closed.\n\n"
                    "Deleting a product available in a session would be like attempting to snatch a"
                    "hamburger from a customer’s hand mid-bite; chaos will ensue as ketchup and mayo go flying everywhere!"))

    def get_product_info_pos(self, price, quantity, pos_config_id):
        self.ensure_one()
        config = self.env['pos.config'].browse(pos_config_id)

        # Tax related
        taxes = self.taxes_id.compute_all(price, config.currency_id, quantity, self)
        grouped_taxes = {}
        for tax in taxes['taxes']:
            if tax['id'] in grouped_taxes:
                grouped_taxes[tax['id']]['amount'] += tax['amount']/quantity if quantity else 0
            else:
                grouped_taxes[tax['id']] = {
                    'name': tax['name'],
                    'amount': tax['amount']/quantity if quantity else 0
                }

        all_prices = {
            'price_without_tax': taxes['total_excluded']/quantity if quantity else 0,
            'price_with_tax': taxes['total_included']/quantity if quantity else 0,
            'tax_details': list(grouped_taxes.values()),
        }

        # Pricelists
        if config.use_pricelist:
            pricelists = config.available_pricelist_ids
        else:
            pricelists = config.pricelist_id
        price_per_pricelist_id = pricelists._price_get(self, quantity) if pricelists else False
        pricelist_list = [{'name': pl.name, 'price': price_per_pricelist_id[pl.id]} for pl in pricelists]

        # Warehouses
        warehouse_list = [
            {'name': w.name,
            'available_quantity': self.with_context({'warehouse': w.id}).qty_available,
            'forecasted_quantity': self.with_context({'warehouse': w.id}).virtual_available,
            'uom': self.uom_name}
            for w in self.env['stock.warehouse'].search([])]

        # Suppliers
        key = itemgetter('partner_id')
        supplier_list = []
        for key, group in groupby(sorted(self.seller_ids, key=key), key=key):
            for s in list(group):
                if not((s.date_start and s.date_start > date.today()) or (s.date_end and s.date_end < date.today()) or (s.min_qty > quantity)):
                    supplier_list.append({
                        'name': s.partner_id.name,
                        'delay': s.delay,
                        'price': s.price
                    })
                    break

        # Variants
        variant_list = [{'name': attribute_line.attribute_id.name,
                         'values': list(map(lambda attr_name: {'name': attr_name, 'search': '%s %s' % (self.name, attr_name)}, attribute_line.value_ids.mapped('name')))}
                        for attribute_line in self.attribute_line_ids]

        return {
            'all_prices': all_prices,
            'pricelists': pricelist_list,
            'warehouses': warehouse_list,
            'suppliers': supplier_list,
            'variants': variant_list
        }
    # * MIKE CODE MODIFICATIONS *
    @api.model
    def create_from_ui(self, payload):
        """ Create or modify a Product from the point of sale ui.
            Product contains the Product's fields. """

        base64_content = payload.get('image_1920', False)
        image = base64_content.split(',', 1)[-1]
        if payload.get('pos_categ_ids') and isinstance(
                payload.get('pos_categ_ids'), str):
            pos_categ_ids = [int(item) for item in
                             payload.get('pos_categ_ids').split(',')]
        else:
            pos_categ_ids = payload.get('pos_categ_ids')
        product_id = payload.get('id')
        values = {
            'name': payload.get('name'),
            'image_1920': image,
            'standard_price': float(
                payload.get('standard_price')) if payload.get(
                'standard_price') else 0,
            'lst_price': float(payload.get('lst_price')) if payload.get(
                'lst_price') else 0,
            'pos_categ_ids': pos_categ_ids if payload.get(
                'pos_categ_ids') and payload.get(
                'pos_categ_ids') != '0' else False,
            'barcode': payload.get('barcode'),
            'default_code': payload.get('default_code'),
            'available_in_pos': True
        }
        if payload.get('image_1920') == "":
            del values['image_1920']
        if product_id:  # Modifying existing product
            self.browse(product_id).write(values)
        else:
            product = self.create(values)
            product_id = product.id
        return product_id


class ProductAttributeCustomValue(models.Model):
    _inherit = "product.attribute.custom.value"

    pos_order_line_id = fields.Many2one('pos.order.line', string="PoS Order Line", ondelete='cascade')


class UomCateg(models.Model):
    _inherit = 'uom.category'

    is_pos_groupable = fields.Boolean(string='Group Products in POS',
        help="Check if you want to group products of this category in point of sale orders")


class Uom(models.Model):
    _inherit = 'uom.uom'

    is_pos_groupable = fields.Boolean(related='category_id.is_pos_groupable', readonly=False)
