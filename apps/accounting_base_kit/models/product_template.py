# -*- coding: utf-8 -*-
import math
from odoo import fields, models, api
from odoo.tools import float_compare


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


def generate_ean(ean):
    """Creates and returns a valid ean13 from an invalid one"""
    if not ean:
        return "0000000000000"
    product_identifier = '00000000000' + ean
    ean = product_identifier[-11:]
    check_number = check_ean(ean + '00')
    return f'{ean}0{check_number}'


class ProductCategory(models.Model):
    """ Inheriting product category to add fields for publish
    product in website """
    _inherit = 'product.category'

    published_count = fields.Integer(string="Published",
                                     compute='_compute_published_count',
                                     help='Total count of published product '
                                          'in website.')
    unpublished_count = fields.Integer(string="Unpublished",
                                       compute='_compute_published_count',
                                       help='Total count of unpublished '
                                            'product in website.')

    def _compute_published_count(self):
        """Function for computing count of published and unpublished products"""
        for rec in self:
            products = self.env['product.template'].search(
                [('categ_id', '=', rec.id)])
            published = products.filtered(lambda product:
                                          product.is_published == True
                                          and product.sale_ok == True)
            unpublished = products.filtered(lambda product:
                                            product.is_published == False
                                            and product.sale_ok == True)
            rec.published_count = len(published)
            rec.unpublished_count = len(unpublished)

    def action_publish_all_products(self):
        """Smart tab function to publish products in website"""
        for rec in self:
            products = self.env['product.template'].search(
                [('categ_id', '=', rec.id)])
            products = products.filtered(lambda product:
                                         product.sale_ok == True)
            for product in products:
                if not product.is_published:
                    product.is_published = True

    def action_nothing(self):
        """ Return true """
        return True


class ProductTemplate(models.Model):
    """Inherited the model for adding new fields and functions"""
    _inherit = 'product.template'

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
        create new product.template"""
        res = super(ProductTemplate, self).create(vals_list)

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
    def action_generate_internal_ref(self):
        """Creating internal reference"""
        active_ids = self.env.context.get('active_ids')
        products = self.env['product.template'].browse(active_ids)
        for rec in products:
            rec.default_code = self.generate_ref(rec)
        return self

    asset_category_id = fields.Many2one('account.asset.category', string='Asset Type', company_dependent=True, ondelete="restrict")
    deferred_revenue_category_id = fields.Many2one('account.asset.category', string='Deferred Revenue Type', company_dependent=True, ondelete="restrict")

    def _get_asset_accounts(self):
        res = super(ProductTemplate, self)._get_asset_accounts()
        if self.asset_category_id:
            res['stock_input'] = self.property_account_expense_id
        if self.deferred_revenue_category_id:
            res['stock_output'] = self.property_account_income_id
        return res

    po_history_line_ids = fields.One2many('purchase.template.history.line',
                                          'history_id',
                                          string='Purchase History',
                                          compute='_compute_po_history_line_ids',
                                          help='Purchased product details')

    def _compute_po_history_line_ids(self):
        """Compute the purchase history lines. It will show all purchase order
         details of the particular product in product.product based on the
          limit and status."""
        self.po_history_line_ids = False
        status = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.po_status')
        limit = int(self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.po_limit'))
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
                ('product_id', 'in', self.product_variant_ids.ids), ('state', 'in', state)
            ], limit=(None if limit == 0 else limit))
            self.env['purchase.template.history.line'].create([
                {
                    'history_id': self.id,
                    'order_date': rec.order_id.date_order,
                    'order_reference_id': rec.order_id.id,
                    'description': rec.name,
                    'price_unit': rec.price_unit,
                    'product_qty': rec.product_qty,
                    'price_subtotal': rec.price_subtotal,
                    'price_total': rec.price_total,
                } for rec in po_order_line
            ])

    so_history_line_ids = fields.One2many('sale.template.history.line',
                                          'history_id',
                                          string='Sale History',
                                          compute='_compute_so_history_line_ids',
                                          help='Sale product variant details')

    def _compute_so_history_line_ids(self):
        """Compute the sale history lines. It will show all sale order
         details of the particular product in product.template based on the
          limit and status."""
        self.so_history_line_ids = False
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
                ('product_id', 'in', self.product_variant_ids.ids), ('state', 'in', state)
            ], limit=(None if limit == 0 else limit))
            self.env['sale.template.history.line'].create([{
                'history_id': self.id,
                'order_date': line.order_id.date_order,
                'order_reference_id': line.order_id.id,
                'description': line.product_id.name,
                'price_unit': line.price_unit,
                'product_qty': line.product_uom_qty,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_total,
            } for line in so_order_line])

    pos_history_line_ids = fields.One2many('pos.template.history.line',
                                           'history_id',
                                           string='Point of Sale History',
                                           compute='_compute_pos_history_line_ids',
                                           help='Point of Sale product variant details')

    def _compute_pos_history_line_ids(self):
        """Compute the point of sale history lines. It will show all pos order
         details of the particular product in product.template based on the
          limit and status"""
        self.pos_history_line_ids = False
        limit = self.env['ir.config_parameter'].sudo().get_param('accounting_base_kit.so_limit')
        if int(limit) >= 0:
            pos_order_line = self.env['pos.order.line'].search([
                ('product_id', 'in', self.product_variant_ids.ids)
            ], limit=(None if limit == 0 else limit))
            self.env['pos.template.history.line'].create([{
                'history_id': self.id,
                'order_date': line.order_id.date_order,
                'order_reference_id': line.order_id.id,
                'description': line.product_id.name,
                'price_unit': line.price_unit,
                'product_qty': line.qty,
                'price_subtotal': line.price_subtotal,
                'price_total': line.price_subtotal_incl,
            } for line in pos_order_line])

    def quick_publish_products(self):
        """ Function for publish product in website shop """
        for rec in self:
            rec.is_published = True if not rec.is_published else False
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_published_product(self):
        """Function on button to publish the product"""
        self.is_published = True

    def action_unpublished_product(self):
        """Function on button to un publish the product"""
        self.is_published = False

    def action_publish(self):
        """ Open a wizard for publish or un publish products
                 based on the selected products."""
        return {
            'name': "Publish/Unpublish Products",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.publish',
            'view_id': self.env.ref('accounting_base_kit.product_publish_view_form').id,
            'target': 'new',
            'context': {
                'default_product_ids': self.env.context.get('active_ids')
            },
        }

