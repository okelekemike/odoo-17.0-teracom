
from odoo import fields, models, tools, _


class ProductProduct(models.Model):
    """Inherited product template to add additional fields and compute methods for quantity computation"""
    _inherit = 'product.product'

    qty_incoming = fields.Float(string='Incoming Qty', compute='_compute_quantities', store=True)
    qty_outgoing = fields.Float(string='Outgoing Qty', compute='_compute_quantities', store=True)
    qty_avail = fields.Float(string='Available Qty', compute='_compute_quantities', store=True)
    qty_virtual = fields.Float(string='Virtual Qty', compute='_compute_quantities', store=True)

    def _compute_quantities_dict(self, lot_id, owner_id, package_id, from_date=False, to_date=False):
        """Function for computing the incoming, outgoing,available, and virtual quantities for the product"""
        res = super()._compute_quantities_dict(lot_id, owner_id, package_id,  from_date=False, to_date=False)
        for product in self.with_context(prefetch_fields=False):
            product_id = product.id
            product.qty_incoming = res[product_id]['incoming_qty']
            product.qty_outgoing = res[product_id]['outgoing_qty']
            product.qty_avail = res[product_id]['qty_available']
            product.qty_virtual = res[product_id]['virtual_available']
        return res


class ProductTemplate(models.Model):
    """Inherited product template to add additional fields and compute methods
     for quantity computation"""
    _inherit = 'product.template'

    qty_incoming = fields.Float(
        string='Incoming Qty', compute='_compute_quantities', store=True, help='Incoming quantity of the product')
    qty_outgoing = fields.Float(
        string='Outgoing Qty', compute='_compute_quantities', store=True, help='Outgoing quantity of the product')
    qty_avail = fields.Float(
        string='Available Qty', compute='_compute_quantities', store=True, help='Available quantity of the product')
    qty_virtual = fields.Float(
        string='Virtual Qty', compute='_compute_quantities', store=True, help='Virtual quantity of the product')

    def _compute_quantities(self):
        """Function for computing the incoming, outgoing,available, and virtual quantities for the product template"""
        res = super()._compute_quantities()
        for template in self:
            template.qty_incoming = template.incoming_qty
            template.qty_outgoing = template.outgoing_qty
            template.qty_avail = template.qty_available
            template.qty_virtual = template.virtual_available
        return res


class StockLocationProduct(models.Model):
    """ Model for generating pivot view based on product locations"""
    _name = 'stock.location.product'
    _description = "Product Location Report"
    _auto = False

    product_id = fields.Many2one('product.template', string="Product", help='Name of the product')
    location_id = fields.Many2one('stock.location', string='Location', help='Choose the location')
    on_hand_qty = fields.Integer(string='On Hand Quantity', help='On hand quantity of the product')
    qty_incoming = fields.Integer(string='Incoming Quantity', help='Incoming quantity of the product')
    qty_outgoing = fields.Integer(string='Outgoing Quantity', help='Outgoing quantity of the product')
    forecast_qty = fields.Integer(string='Forecast Quantity', help='Forecasted quantity of the product')

    def init(self):
        """Initialize the view. Drops the existing view if it exists and
        creates a new view with the following columns for the Product model"""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            ''' CREATE OR REPLACE VIEW %s AS (
                SELECT row_number() OVER () AS id,
                    product_template.id AS product_id,
                    stock_location.id AS location_id,
                    SUM(stock_quant.quantity) AS on_hand_qty,
                    SUM(stock_quant.quantity + product_template.qty_incoming - product_template.qty_outgoing) AS forecast_qty,
                    SUM(product_template.qty_incoming) AS qty_incoming,
                    SUM(product_template.qty_outgoing) AS qty_outgoing
                FROM product_template
                INNER JOIN product_product ON product_product.product_tmpl_id = product_template.id
                INNER JOIN stock_quant ON stock_quant.product_id = product_product.id
                INNER JOIN stock_location ON stock_quant.location_id = stock_location.id
                WHERE stock_location.usage = 'internal'
                GROUP BY product_template.id, stock_location.id)''' % (self._table,))


class StockLocationProductVariant(models.Model):
    """ Model for generating pivot view for product variants based on product locations"""
    _name = 'stock.location.product.variant'
    _description = "Product Variant Location Report"
    _auto = False

    product_id = fields.Many2one('product.product', string="Product", help='Name of the product')
    location_id = fields.Many2one('stock.location', string='Location', help='Choose the location')
    on_hand_qty = fields.Integer(string='On Hand Quantity', help='On hand quantity of the product')
    qty_incoming = fields.Integer(string='Incoming Quantity', help='Incoming quantity of the product')
    qty_outgoing = fields.Integer(string='Outgoing Quantity', help='Outgoing quantity of the product')
    forecast_qty = fields.Integer(string='Forecast Quantity', help='Forecasted quantity of the product')

    def init(self):
        """Initialize the view. Drops the existing view if it exists and
        creates a new view with the following columns for the Product variant
        model"""
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute(
            ''' CREATE OR REPLACE VIEW %s AS (
                SELECT row_number() OVER () AS id, 
                    stock_quant.product_id, 
                    stock_quant.location_id, 
                    stock_quant.quantity on_hand_qty, 
                    (stock_quant.quantity + product_product.qty_incoming - product_product.qty_outgoing) AS forecast_qty, 
                    product_product.qty_incoming,
                    product_product.qty_outgoing 
                FROM product_product 
                INNER JOIN stock_quant ON stock_quant.product_id = product_product.id
                INNER JOIN product_template ON product_product.product_tmpl_id = product_template.id
                INNER JOIN stock_location ON stock_quant.location_id = stock_location.id
                WHERE stock_location.usage = 'internal')''' % (self._table,))
