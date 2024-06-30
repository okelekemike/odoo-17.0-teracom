# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models


class ScrapManagement(models.Model):
    """ This class define a new model for scrap management."""
    _name = "scrap.management"
    _description = "Company Scrap Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'scrap_management_number'

    scrap_management_number = fields.Char(
        string="Scrap Number", readonly=True, required=True, copy=False,
        default="New", help="Field to specify sequence number")
    scrap_order_id = fields.Many2one(
        'stock.scrap', string="Scrap Order", required=True,
        help="Field to choose  scrap order",
        domain="[('state', '=','done'),"
               "('typ_of_reuse','=','dismantle'),"
               "('state_management', '=','none')]")
    bill_of_material_id = fields.Many2one(
        'mrp.bom', related="scrap_order_id.bill_of_material_id",
        string="Bill of Material", help="Field to choose bill of material")
    product_id = fields.Many2one(
        'product.product',
        string="Product", related="scrap_order_id.product_id",
        help="Field to choose product")
    date = fields.Date(string="Date", help="field to give the date")
    qty = fields.Float(string="Quantity", related="scrap_order_id.scrap_qty",
                       help="Field to specify quantity")
    scrap_management_line_ids = fields.One2many(
        'scrap.management.line', 'scrap_management_id',
        string="Components", help="Field to specify components")
    location_id = fields.Many2one(
        'stock.location', string="Transfer location",
        domain="[('usage','=','internal')]", required=True,
        help="Field to specify location")
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirm'), ('done', 'Done')],
        string="State", default="draft",
        help="Field to specify state of Scrap Management")

    @api.model_create_multi
    def create(self, vals_list):
        """
           Summary:
               function return sequence number for record
           Args:
               vals:To store the sequence created
           return:
                result:return sequence created
         """
        for vals in vals_list:
            if vals.get('scrap_management_number', 'New') == 'New':
                vals['scrap_management_number'] = self.env['ir.sequence'].next_by_code(
                    'scrap.management') or 'New'
        result = super(ScrapManagement, self).create(vals_list)
        return result

    def action_confirm(self):
        """Function to confirm the Scrap Management and add value to one2many"""
        for line in self.bill_of_material_id.bom_line_ids:
            if line.product_id.detailed_type not in ['consu', 'service']:
                self.write({'scrap_management_line_ids': [
                        (0, 0, {'product_id': line.product_id.id, 'dismantle_qty': (self.qty * line.product_qty)})
                    ],})
        self.write({'state': 'confirm'})

    def action_done(self):
        """Function to done the Scrap Management and
        add product move and stock quantity"""
        self.env['stock.quant'].create({
            'location_id': self.scrap_order_id.scrap_location_id.id,
            'product_id': self.product_id.id,
            'quantity': 0 - self.qty
        })
        for line in self.scrap_management_line_ids:
            scrap_qty = line.dismantle_qty - line.useful_qty
            if line.useful_qty > 0:
                self.env['stock.quant'].create({
                    'location_id': self.location_id.id,
                    'product_id': line.product_id.id,
                    'quantity': line.useful_qty
                })
                self.env['stock.move.line'].create({
                    'reference': self.scrap_management_number,
                    'product_id': line.product_id.id,
                    'location_dest_id': self.location_id.id,
                    'quantity': line.useful_qty,
                    'company_id': self.env.company.id,
                    'location_id': self.scrap_order_id.scrap_location_id.id,
                    'state': "done"
                })
            if scrap_qty > 0:
                self.env['stock.quant'].create({
                    'location_id': self.scrap_order_id.scrap_location_id.id,
                    'product_id': line.product_id.id,
                    'quantity': scrap_qty
                })
                self.env['stock.move.line'].create({
                    'reference': self.scrap_management_number,
                    'product_id': line.product_id.id,
                    'quantity': scrap_qty,
                    'location_id': self.scrap_order_id.scrap_location_id.id,
                    'company_id': self.env.company.id,
                    'state': "done",
                    'location_dest_id': self.scrap_order_id.scrap_location_id.id
                })
        self.write({'state': "done"})
        self.scrap_order_id.write({'state_management': "dismantled"})
        self.date = date.today()

    def action_product_moves(self):
        """Function to return the product moves"""
        return {
            'name': "Product Moves",
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'stock.move.line',
            'domain': [('reference', '=', self.scrap_management_number)]}
