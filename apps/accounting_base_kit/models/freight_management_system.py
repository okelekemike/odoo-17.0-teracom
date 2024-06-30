# -*- coding: utf-8 -*-
from werkzeug import urls
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class CustomClearanceRevision(models.Model):
    """Allows custom clearance for freight orders"""
    _name = 'clearance.revision'
    _description = 'Custom Clearance Revision'

    name = fields.Char(string='Name', help='Name of the revision')
    reason = fields.Text(string='Reason', help='Reason for revision')
    clearance_id = fields.Many2one('custom.clearance',
                                   string='Custom Clearance',
                                   help='Relation from custom clearance')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class CustomClearance(models.Model):
    """Model for custom clearance"""
    _name = 'custom.clearance'
    _description = 'Custom Clearance'

    name = fields.Char(string='Name', compute='_compute_name',
                       help='Name of custom clearance')
    freight_id = fields.Many2one('freight.order', required=True,
                                 string='Freight Order',
                                 help='Select the freight order')
    date = fields.Date(string='Date', help='Date of clearance')
    agent_id = fields.Many2one('res.partner', string='Agent', required=True,
                               help='Select the agent for the clearance')
    loading_port_id = fields.Many2one('freight.port', string="Loading Port",
                                      help='Select the port for loading')
    discharging_port_id = fields.Many2one('freight.port',
                                          string="Discharging Port",
                                          help='Specify the discharging port')
    line_ids = fields.One2many('custom.clearance.line', 'clearance_id',
                               string='Clearance Line',
                               help='Line for adding the document')
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
                              ('done', 'Done')],
                             default='draft', string="State",
                             help='Different states of custom clearance')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.depends('freight_id')
    def _compute_name(self):
        """Compute the name of custom clearance"""
        for freight in self:
            freight.name = 'CC - ' + str(
                freight.freight_id.name) if freight.freight_id else 'CC - '

    @api.onchange('freight_id')
    def _onchange_freight_id(self):
        """Getting default values for loading and discharging port"""
        for rec in self:
            rec.date = rec.freight_id.order_date
            rec.loading_port_id = rec.freight_id.loading_port_id
            rec.discharging_port_id = rec.freight_id.discharging_port_id
            rec.agent_id = rec.freight_id.agent_id

    def action_confirm(self):
        """Send mail to inform agents to custom clearance is confirmed"""
        for rec in self:
            rec.name = 'CC' \
                       ' - ' + rec.freight_id.name
            rec.state = 'confirm'
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=custom.clearance&view_type=form' % {
                                     'id': self.id})
            Urls_ = urls.url_join(base_url,
                                  'web#id=%(id)s&model=freight.order&view_type=form' % {
                                      'id': self.freight_id.id})
            mail_content = _('Hi %s,<br>'
                             'The Custom Clearance %s is confirmed'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;'
                             'text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; '
                             'background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;'
                             'text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; '
                             'background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % (rec.agent_id.name, rec.name, Urls,
                                  rec.name, Urls_, self.freight_id.name)
            main_content = {
                'subject': _('Custom Clearance For %s') % self.freight_id.name,
                'author_id': self.env.user.partner_id.id,
                'body_html': mail_content,
                'email_to': rec.agent_id.email,
            }
            mail_id = self.env['mail.mail'].create(main_content)
            mail_id.mail_message_id.body = mail_content
            mail_id.send()

    def action_revision(self):
        """Creating custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Received/Delivered',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'custom.clearance.revision',
            'context': {
                'default_custom_id': self.id
            }
        }

    def action_get_revision(self):
        """Getting details of custom revision"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Revision',
            'view_mode': 'tree,form',
            'res_model': 'custom.clearance.revision',
            'domain': [('custom_id', '=', self.id)],
            'context': "{'create': False}"
        }


class CustomClearanceLine(models.Model):
    """Uploading the documents for custom clearance"""
    _name = 'custom.clearance.line'
    _description = 'Custom Clearance Line'

    name = fields.Char(string='Document Name',
                       help='Name of the document attaching')
    document = fields.Binary(string="Documents", store=True, attachment=True,
                             help='Upload the document')
    clearance_id = fields.Many2one('custom.clearance',
                                   string='Custom Clearance',
                                   help='Relation from custom clearance')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightContainer(models.Model):
    """Model for creating the containers for freight"""
    _name = 'freight.container'
    _description = 'Freight Container'

    name = fields.Char(string='Name', required=True,
                       help='Name of the container')
    code = fields.Char(string='Code', help='Code for the container')
    size = fields.Float(string='Size', required=True,
                        help='Size of the container')
    size_uom_id = fields.Many2one('uom.uom', string='Size UOM',
                                  help='The unit of measure of selected size')
    weight = fields.Float(string='Weight', required=True,
                          help='The weight capacity of container')
    weight_uom_id = fields.Many2one('uom.uom', string='Weight UOM',
                                    help='The unit of measure of selected'
                                         'weight')
    volume = fields.Float(string='Volume', required=True,
                          help='Volume of the container')
    volume_uom_id = fields.Many2one('uom.uom', string='Volume UOM',
                                    help='The unit of measure of the volume')
    active = fields.Boolean(string='Active', default=True,
                            help='Make it active or inactive')
    state = fields.Selection([('available', 'Available'),
                              ('reserve', 'Reserve')], default='available',
                             help='Select the state')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightOrder(models.Model):
    """Model for creating freight orders"""
    _name = 'freight.order'
    _description = 'Freight Order'

    name = fields.Char(string='Name', default='New', readonly=True,
                       help='Name of the order')
    shipper_id = fields.Many2one('res.partner', string='Shipper', required=True,
                                 help="Shipper's Details")
    consignee_id = fields.Many2one('res.partner', 'Consignee',
                                   help="Select the consignee for the order")
    type = fields.Selection([('import', 'Import'), ('export', 'Export')],
                            string='Import/Export', required=True,
                            help="Type of freight operation")
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], string='Transport',
                                      help='Type of transportation',
                                      required=True)
    land_type = fields.Selection([('ltl', 'LTL'), ('ftl', 'FTL')],
                                 string='Land Shipping',
                                 help="Types of shipment movement involved in"
                                      "Land")
    water_type = fields.Selection([('fcl', 'FCL'), ('lcl', 'LCL')],
                                  string='Water Shipping',
                                  help="Types of shipment movement involved in"
                                       "Water")
    order_date = fields.Date(string='Date', default=fields.Date.today(),
                             help="Date of order")
    loading_port_id = fields.Many2one('freight.port', string="Loading Port",
                                      required=True,
                                      help="Loading port of the freight order")
    discharging_port_id = fields.Many2one('freight.port',
                                          string="Discharging Port",
                                          required=True,
                                          help="Discharging port of freight"
                                               "order")
    state = fields.Selection([('draft', 'Draft'), ('submit', 'Submitted'),
                              ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'), ('done', 'Done'),
                              ('cancel', 'Cancel')],
                             default='draft', string="State",
                             help='Different states of freight order')
    clearance = fields.Boolean(string='Clearance', help='Checking the'
                                                        'clearance')
    clearance_count = fields.Integer(compute='_compute_count',
                                     string='Clearance Count',
                                     help='The number of clearance')
    invoice_count = fields.Integer(compute='_compute_count',
                                   string='Invoice Count',
                                   help='The number invoice created')
    total_order_price = fields.Float(string='Total',
                                     compute='_compute_total_order_price',
                                     help='The total order price')
    total_volume = fields.Float(string='Total Volume',
                                compute='_compute_total_order_price',
                                help='The total used volume')
    total_weight = fields.Float(string='Total Weight',
                                compute='_compute_total_order_price',
                                help='The total weight used')
    order_ids = fields.One2many('freight.order.line', 'order_id',
                                string='Freight Order Line',
                                help='The freight order lines of the order')
    route_ids = fields.One2many('freight.order.routes.line', 'freight_id',
                                string='Route', help='The route of order')
    total_route_sale = fields.Float(string='Total Sale',
                                    compute="_compute_total_route_cost",
                                    help='The total cost of sale')
    service_ids = fields.One2many('freight.order.service', 'freight_id',
                                  string="Service", help='Service of the order')
    total_service_sale = fields.Float(string='Service Total Sale',
                                      compute="_compute_total_service_cost",
                                      help='The total service cost of order')
    agent_id = fields.Many2one('res.partner', string='Agent',
                               required=True, help="Details of agent")
    expected_date = fields.Date(string='Expected Date', help='The expected date'
                                                             'of the order')
    track_ids = fields.One2many('freight.track', 'freight_id',
                                string='Tracking', help='For tracking the'
                                                        'freight orders')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.depends('order_ids.total_price', 'order_ids.volume',
                 'order_ids.weight')
    def _compute_total_order_price(self):
        """Computing the price of the order"""
        for rec in self:
            rec.total_order_price = sum(rec.order_ids.mapped('total_price'))
            rec.total_volume = sum(rec.order_ids.mapped('volume'))
            rec.total_weight = sum(rec.order_ids.mapped('weight'))

    @api.depends('route_ids.sale')
    def _compute_total_route_cost(self):
        """Computing the total cost of route operation"""
        for rec in self:
            rec.total_route_sale = sum(rec.route_ids.mapped('sale'))

    @api.depends('service_ids.total_sale')
    def _compute_total_service_cost(self):
        """Computing the total cost of services"""
        for rec in self:
            rec.total_service_sale = sum(rec.service_ids.mapped('total_sale'))

    @api.model_create_multi
    def create(self, vals_list):
        """Create Sequence for multiple records"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'freight.order.sequence')
        return super(FreightOrder, self).create(vals_list)

    def action_create_custom_clearance(self):
        """Create custom clearance"""
        clearance = self.env['custom.clearance'].create({
            'name': 'CC - ' + self.name,
            'freight_id': self.id,
            'date': self.order_date,
            'loading_port_id': self.loading_port_id.id,
            'discharging_port_id': self.discharging_port_id.id,
            'agent_id': self.agent_id.id,
        })
        result = {
            'name': 'action.name',
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': clearance.id,
            'res_model': 'custom.clearance',
        }
        self.clearance = True
        return result

    def get_custom_clearance(self):
        """Get custom clearance"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Custom Clearance',
            'view_mode': 'tree,form',
            'res_model': 'custom.clearance',
            'domain': [('freight_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_track_order(self):
        """Track the order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Received/Delivered',
            'view_mode': 'form',
            'target': 'new',
            'res_model': 'freight.order.track',
            'context': {
                'default_freight_id': self.id
            }
        }

    def action_create_invoice(self):
        """Create invoice"""
        lines = []
        if self.order_ids:
            for order in self.order_ids:
                value = (0, 0, {
                    'name': order.product_id.name,
                    'price_unit': order.price,
                    'quantity': order.volume + order.weight,
                })
                lines.append(value)
        if self.route_ids:
            for route in self.route_ids:
                value = (0, 0, {
                    'name': route.routes_id.name,
                    'price_unit': route.sale,
                })
                lines.append(value)
        if self.service_ids:
            for service in self.service_ids:
                value = (0, 0, {
                    'name': service.service_id.name,
                    'price_unit': service.sale,
                    'quantity': service.qty
                })
                lines.append(value)
        invoice_line = {
            'move_type': 'out_invoice',
            'partner_id': self.shipper_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'ref': self.name,
            'invoice_line_ids': lines,
        }
        inv = self.env['account.move'].create(invoice_line)
        result = {
            'name': 'action.name',
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': inv.id,
            'res_model': 'account.move',
        }
        self.state = 'invoice'
        return result

    def action_cancel(self):
        """Cancel the record"""
        if self.state == 'draft' and self.state == 'submit':
            self.state = 'cancel'
        else:
            raise ValidationError("You can't cancel this order")

    def get_invoice(self):
        """View the invoice"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invoice',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('ref', '=', self.name)],
            'context': "{'create': False}"
        }

    @api.depends('name')
    def _compute_count(self):
        """Compute custom clearance and account move's count"""
        for rec in self:
            if rec.env['custom.clearance'].search(
                    [('freight_id', '=', rec.id)]):
                rec.clearance_count = rec.env['custom.clearance'].search_count(
                    [('freight_id', '=', rec.id)])
            else:
                rec.clearance_count = 0
            if rec.env['account.move'].search([('ref', '=', rec.name)]):
                rec.invoice_count = rec.env['account.move'].search_count(
                    [('ref', '=', rec.name)])
            else:
                rec.invoice_count = 0

    def action_submit(self):
        """Submitting order"""
        for rec in self:
            rec.state = 'submit'
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=freight.order&view_type=form' % {
                                     'id': self.id})
            mail_content = _('Hi %s,<br>'
                             'The Freight Order %s is Submitted'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; margin-bottom: 0px; '
                             'font-weight: 400;text-align: center; '
                             'vertical-align: middle; cursor: pointer; '
                             'white-space: nowrap; background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % (rec.agent_id.name, rec.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (self.shipper_id.id, self.consignee_id.id,
                              self.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is Submitted') % self.name,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = self.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()

    def action_confirm(self):
        """Confirm order"""
        for rec in self:
            custom_clearance = self.env['custom.clearance'].search([
                ('freight_id', '=', self.id)])
            if custom_clearance:
                for clearance in custom_clearance:
                    if clearance.state == 'confirm':
                        rec.state = 'confirm'
                        base_url = self.env['ir.config_parameter'].sudo().get_param(
                            'web.base.url')
                        Urls = urls.url_join(base_url,
                                             'web#id=%(id)s&model=freight.order&view_type=form' % {
                                                 'id': self.id})
                        mail_content = _('Hi %s,<br> '
                                         'The Freight Order %s is Confirmed '
                                         '<div style = "text-align: center; '
                                         'margin-top: 16px;"><a href = "%s"'
                                         'style = "padding: 5px 10px; '
                                         'font-size: 12px; line-height: 18px; '
                                         'color: #FFFFFF; border-color:#875A7B; '
                                         'text-decoration: none; '
                                         'display: inline-block; '
                                         'margin-bottom: 0px; font-weight: 400;'
                                         'text-align: center; '
                                         'vertical-align: middle; '
                                         'cursor: pointer; white-space: nowrap; '
                                         'background-image: none; '
                                         'background-color: #875A7B; '
                                         'border: 1px solid #875A7B; '
                                         'border-radius:3px;">'
                                         'View %s</a></div>'
                                         ) % (rec.agent_id.name, rec.name,
                                              Urls, rec.name)
                        email_to = self.env['res.partner'].search([
                            ('id', 'in', (self.shipper_id.id,
                                          self.consignee_id.id, self.agent_id.id))])
                        for mail in email_to:
                            main_content = {
                                'subject': _(
                                    'Freight Order %s is Confirmed') % self.name,
                                'author_id': self.env.user.partner_id.id,
                                'body_html': mail_content,
                                'email_to': mail.email
                            }
                            mail_id = self.env['mail.mail'].create(main_content)
                            mail_id.mail_message_id.body = mail_content
                            mail_id.send()
                    elif clearance.state == 'draft':
                        raise ValidationError("the custom clearance ' %s ' is "
                                              "not confirmed" % clearance.name)
            else:
                raise ValidationError(
                    "Create a custom clearance for %s" % rec.name)
            for line in rec.order_ids:
                line.container_id.state = 'reserve'

    def action_done(self):
        """Mark order as done"""
        for rec in self:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=freight.order&view_type=form' % {
                                     'id': self.id})
            mail_content = _('Hi %s,<br>'
                             'The Freight Order %s is Completed'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;'
                             'text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; '
                             'background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % (rec.agent_id.name, rec.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (self.shipper_id.id, self.consignee_id.id,
                              self.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is completed') % self.name,
                    'author_id': self.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = self.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()
            self.state = 'done'
            for line in rec.order_ids:
                line.container_id.state = 'available'


class FreightOrderLine(models.Model):
    """Freight order lines are defined"""
    _name = 'freight.order.line'
    _description = 'Freight Order Line'

    order_id = fields.Many2one('freight.order', string="Freight Order",
                               help="Reference from freight order")
    container_id = fields.Many2one('freight.container', string='Container',
                                   domain="[('state', '=', 'available')]",
                                   help='The freight container')
    product_id = fields.Many2one('product.product', string='Goods',
                                 help='The Freight Products')
    billing_type = fields.Selection([('weight', 'Weight'),
                                     ('volume', 'Volume')], string="Billing On",
                                    help='Select the billing type for'
                                         'calculating the total amount')
    pricing_id = fields.Many2one('freight.price', string='Pricing',
                                 help='The pricing of order')
    price = fields.Float(string='Unit Price', help='Unit price of the selected'
                                                   'goods')
    total_price = fields.Float(string='Total Price', help='This will be the'
                                                          'total price')
    volume = fields.Float(string='Volume', help='Volume of the goods')
    weight = fields.Float(string='Weight', help='Weight of the goods')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.constrains('weight')
    def _check_weight(self):
        """Checking the weight of containers"""
        for rec in self:
            if rec.container_id and rec.billing_type:
                if rec.billing_type == 'weight':
                    if rec.container_id.weight < rec.weight:
                        raise ValidationError(
                            'The weight is must be less '
                            'than or equal to %s' % (rec.container_id.weight))

    @api.constrains('volume')
    def _check_volume(self):
        """Checking the volume of containers"""
        for rec in self:
            if rec.container_id and rec.billing_type:
                if rec.billing_type == 'volume':
                    if rec.container_id.volume < rec.volume:
                        raise ValidationError(
                            'The volume is must be less '
                            'than or equal to %s' % (rec.container_id.volume))

    @api.onchange('pricing_id', 'billing_type')
    def _onchange_price(self):
        """Calculate the weight and volume of container"""
        for rec in self:
            if rec.billing_type == 'weight':
                rec.volume = 0.00
                rec.price = rec.pricing_id.weight
            elif rec.billing_type == 'volume':
                rec.weight = 0.00
                rec.price = rec.pricing_id.volume

    @api.onchange('pricing_id', 'billing_type', 'volume', 'weight')
    def _onchange_total_price(self):
        """Calculate sub total price"""
        for rec in self:
            if rec.billing_type and rec.pricing_id:
                if rec.billing_type == 'weight':
                    rec.total_price = rec.weight * rec.price
                elif rec.billing_type == 'volume':
                    rec.total_price = rec.volume * rec.price


class FreightOrderRoutesLine(models.Model):
    """Defining the routes for the shipping, also we can add the operations for
    the routes."""
    _name = 'freight.order.routes.line'
    _description = 'Freight Order Routes Lines'

    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 help='Relation from freight order')
    routes_id = fields.Many2one('freight.routes', required=True,
                                string='Routes', help='Select route of freight')
    source_loc_id = fields.Many2one('freight.port', string='Source Location',
                                    help='Select the source port')
    destination_loc_id = fields.Many2one('freight.port',
                                         string='Destination Location',
                                         help='Select the destination port')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], string="Transport",
                                      required=True,
                                      help='Select the transporting medium')
    sale = fields.Float(string='Sale', help="Set the price for Land")
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.onchange('routes_id', 'transport_type')
    def _onchange_routes_id(self):
        """Calculate the price of route operation"""
        for rec in self:
            if rec.routes_id and rec.transport_type:
                if rec.transport_type == 'land':
                    rec.sale = rec.routes_id.land_sale
                elif rec.transport_type == 'air':
                    rec.sale = rec.routes_id.air_sale
                elif rec.transport_type == 'water':
                    rec.sale = rec.routes_id.water_sale


class FreightOrderServiceLine(models.Model):
    """Services in freight orders"""
    _name = 'freight.order.service'
    _description = 'Freight Order Service'

    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 help='Relation from freight order')
    service_id = fields.Many2one('freight.service', required=True,
                                 string='Service', help='Select the service')
    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 help='Select the partner for the service')
    qty = fields.Float(string='Quantity', help='How many Quantity required')
    cost = fields.Float(string='Cost', help='The cost price of the service')
    sale = fields.Float(string='Sale', help='Sale price of the service')
    total_sale = fields.Float('Total Sale', help='The total sale price')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    @api.onchange('service_id', 'partner_id')
    def _onchange_partner_id(self):
        """Calculate the price of services"""
        for rec in self:
            if rec.service_id:
                if rec.partner_id:
                    if rec.service_id.line_ids:
                        for service in rec.service_id.line_ids:
                            if rec.partner_id == service.partner_id:
                                rec.sale = service.sale
                            else:
                                rec.sale = rec.service_id.sale_price
                    else:
                        rec.sale = rec.service_id.sale_price
                else:
                    rec.sale = rec.service_id.sale_price

    @api.onchange('qty', 'sale')
    def _onchange_qty(self):
        """Calculate the subtotal of route operation"""
        for rec in self:
            rec.total_sale = rec.qty * rec.sale


class Tracking(models.Model):
    """Tracking the freight order"""
    _name = 'freight.track'
    _description = 'Freight Track'

    source_loc_id = fields.Many2one('freight.port', string='Source Location',
                                    help='Select the source location of port')
    destination_loc_id = fields.Many2one('freight.port',
                                         string='Destination Location',
                                         help='Destination location of the port')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], string='Transport',
                                      help='Transporting medium of the order')
    freight_id = fields.Many2one('freight.order', string='Freight Order',
                                 help='Reference from freight order')
    date = fields.Date(string='Date', help='Select the date')
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')],
                            string='Received/Delivered',
                            help='Status of the order')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightTracking(models.Model):
    _name = 'freight.order.track'
    _description = 'Freight Order Track'

    date = fields.Date('Date', default=fields.Date.today())
    freight_id = fields.Many2one('freight.order')
    source_loc_id = fields.Many2one('freight.port', 'Source Location')
    destination_loc_id = fields.Many2one('freight.port', 'Destination Location')
    transport_type = fields.Selection([('land', 'Land'), ('air', 'Air'),
                                       ('water', 'Water')], "Transport")
    type = fields.Selection([('received', 'Received'),
                             ('delivered', 'Delivered')], 'Received/Delivered')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)

    def action_order_submit(self):
        """Create tracking details of order"""
        self.env['freight.track'].create({
            'freight_id': self.freight_id.id,
            'source_loc_id': self.source_loc_id.id,
            'destination_loc_id': self.destination_loc_id.id,
            'transport_type': self.transport_type,
            'date': self.date,
            'type': self.type,
        })
        for rec in self.freight_id:
            base_url = self.env['ir.config_parameter'].sudo().get_param(
                'web.base.url')
            Urls = urls.url_join(base_url,
                                 'web#id=%(id)s&model=freight.order&view_type=form' % {
                                     'id': self.id})

            mail_content = _('Hi<br>'
                             'The Freight Order %s is %s at %s'
                             '<div style = "text-align: center; '
                             'margin-top: 16px;"><a href = "%s"'
                             'style = "padding: 5px 10px; font-size: 12px; '
                             'line-height: 18px; color: #FFFFFF; '
                             'border-color:#875A7B;text-decoration: none; '
                             'display: inline-block; '
                             'margin-bottom: 0px; font-weight: 400;'
                             'text-align: center; vertical-align: middle; '
                             'cursor: pointer; white-space: nowrap; '
                             'background-image: none; '
                             'background-color: #875A7B; '
                             'border: 1px solid #875A7B; border-radius:3px;">'
                             'View %s</a></div>'
                             ) % (rec.name, self.type,
                                  self.destination_loc_id.name, Urls, rec.name)
            email_to = self.env['res.partner'].search([
                ('id', 'in', (rec.shipper_id.id, rec.consignee_id.id,
                              rec.agent_id.id))])
            for mail in email_to:
                main_content = {
                    'subject': _('Freight Order %s is %s at %s') % (rec.name,
                                                                    self.type,
                                                                    self.destination_loc_id.name,),
                    'author_id': rec.env.user.partner_id.id,
                    'body_html': mail_content,
                    'email_to': mail.email
                }
                mail_id = rec.env['mail.mail'].create(main_content)
                mail_id.mail_message_id.body = mail_content
                mail_id.send()


class FreightPort(models.Model):
    """Creating different port location for managing freight"""
    _name = 'freight.port'
    _description = 'Freight Port'

    name = fields.Char(string='Name', help='Name for the port')
    code = fields.Char(string='Code', help='Specify a code for freight')
    state_id = fields.Many2one('res.country.state', string='State',
                               domain="[('country_id', '=', country_id)]",
                               help='The State in which port located')
    country_id = fields.Many2one('res.country', required=True,
                                 string='Country',
                                 help='The Country in which port located')
    active = fields.Boolean(string='Active', default=True,
                            help='For activate the Port')
    land = fields.Boolean(string='Land', help='Enable it if the medium is Land')
    air = fields.Boolean(string='Air', help='Enable it if the medium is Air')
    water = fields.Boolean(string='Water',
                           help='Enable it if the medium is Water')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightPrice(models.Model):
    """Freight Pricing"""
    _name = 'freight.price'
    _description = 'Freight Price'

    name = fields.Char(string='Name', required=True, help='Name of the pricing')
    volume = fields.Float(string='Volume Price', required=True,
                          help='Pricing according to Volume')
    weight = fields.Float(string='Weight Price', required=True,
                          help='Pricing according to Weight')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightRoutes(models.Model):
    """Creating the routes for the freight"""
    _name = 'freight.routes'
    _description = 'Freight Routes'

    name = fields.Char(string='Name', required=True, help='Name of the route')
    active = fields.Boolean(string='Active', default=True,
                            help='For activating the route')
    land_sale = fields.Float(string='Land Sale Price', required=True,
                             help='Sale price for land')
    air_sale = fields.Float(string='Air Sale Price', required=True,
                            help='Sale price for Air')
    water_sale = fields.Float(string='Water Sale Price', required=True,
                              help='Sale price for Air')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightService(models.Model):
    """For Creating services available for freight"""
    _name = 'freight.service'
    _description = 'Freight Service'

    name = fields.Char(string='Name', required=True, help='Name of service')
    sale_price = fields.Float(string='Sale Price', required=True,
                              help='Sale price of the service')
    line_ids = fields.One2many('freight.service.line', 'service_id',
                               string='Service Lines',
                               help="Service lines corresponding to a service")
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)


class FreightServiceLine(models.Model):
    _name = 'freight.service.line'
    _description = 'Freight Service Line'

    partner_id = fields.Many2one('res.partner', string="Vendor",
                                 help='Partner corresponding to the service')
    sale = fields.Float(string='Sale Price',
                        help='Mention the price for the service')
    service_id = fields.Many2one('freight.service', string='Service',
                                 help='Relation from freight service')
    company_id = fields.Many2one('res.company', string='Company',
                                 copy=False, readonly=True,
                                 help="Current company",
                                 default=lambda
                                     self: self.env.company.id)
