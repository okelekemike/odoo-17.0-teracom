# -*- coding: utf-8 -*-

import io
import json
from odoo import fields, models, _
from odoo.tools import date_utils, groupby

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class StockLocation(models.TransientModel):
    """Transient model to give the input values for the
    generation of report values"""
    _name = "stock.location.report"
    _description = "Stock Location Report Wizard"

    report_type = fields.Selection([
        ('product', 'Products'),
        ('product_variant', 'Product Variant')
    ], string="Report Type", default='product',
        help="Choose the product type")
    product_variant_id = fields.Many2one(
        'product.product', string="Product Variant",
        help="choose the product variant of which the detail should be known")
    product_id = fields.Many2one(
        'product.template', string="Product",
        help="choose the product of which the detail should be known")

    def action_pdf_report(self):
        """ To pass values in wizard"""
        data = {
            'model_id': self.id,
            'report_type': self.report_type,
            'product_id': self.product_id.id,
            'product_variant_id': self.product_variant_id.id,
        }
        return self.env.ref(
            'accounting_base_kit.stock_by_location_report').report_action(None, data=data)

    def action_xlsx_report(self):
        """ To print the XLSX report type"""
        query = self.env[
            'report.accounting_base_kit.report_stock_location'
        ].query_data(
            self.report_type, self.product_id.id, self.product_variant_id.id)
        data = {
            'report_type': self.report_type,
            'product_id': self.product_id.id,
            'product_variant_id': self.product_variant_id.id,
            'var': query
        }
        return {
            'type': 'ir.actions.report',
            'data': {'model': 'stock.location.report',
                     'options': json.dumps(data, default=date_utils.json_default),
                     'output_format': 'xlsx',
                     'report_name': 'Stock Location',
                     },
            'report_type': 'xlsx',
        }

    def get_xlsx_report(self, data, response):
        """To get the report values for xlsx report"""
        query_result = data['var']
        grouped_data = {}
        for product_id, group in groupby(query_result,
                                         key=lambda x: x['product']['en_US']):
            grouped_data[product_id] = list(group)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        cell_format = workbook.add_format(
            {'font_size': '12px', 'bold': True, 'align': 'center'})
        grey_cell_format = workbook.add_format(
            {'bold': True, 'bg_color': '#D3D3D3', 'align': 'center'})
        head = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '20px',
             'bg_color': 'gray', })
        txt = workbook.add_format({'font_size': '10px', 'align': 'left'})
        txt_head = workbook.add_format({'font_size': '10px', 'align': 'left',
                                        'bold': True})
        sheet.set_column(0, 0, 25)
        sheet.set_column(1, 1, 25)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        sheet.set_column(4, 4, 15)
        sheet.set_column(5, 5, 15)
        sheet.merge_range('A1:B1', 'Report Date:' + str(fields.Date.today()),
                          txt_head)
        sheet.merge_range('A2:F3', 'STOCK LOCATION REPORT', head)
        sheet.write('A6', 'Product', grey_cell_format)
        sheet.write('B6', 'Location', grey_cell_format)
        sheet.write('C6', 'Onhand Qty', grey_cell_format)
        sheet.write('D6', 'Incoming Qty', grey_cell_format)
        sheet.write('E6', 'Outgoing Qty', grey_cell_format)
        sheet.write('F6', 'Forecast Qty', grey_cell_format)
        row = 6
        for product_id, product_data in grouped_data.items():
            for data in product_data:
                sheet.write(row, 0, product_id)
                sheet.write(row, 1, data['location'])
                sheet.write(row, 2, data['on_hand_qty'])
                sheet.write(row, 3, data['qty_incoming'])
                sheet.write(row, 4, data['qty_outgoing'])
                sheet.write(row, 5, data['forecast_qty'])
                row += 1
            sheet.write(row, 0, 'Total:', grey_cell_format)
            sheet.write(row, 1, '', grey_cell_format)
            sheet.write(row, 2, sum(x['on_hand_qty'] for x in product_data), grey_cell_format)
            sheet.write(row, 3, sum(x['qty_incoming'] for x in product_data), grey_cell_format)
            sheet.write(row, 4, sum(x['qty_outgoing'] for x in product_data), grey_cell_format)
            sheet.write(row, 5, sum(x['forecast_qty'] for x in product_data), grey_cell_format)
            row += 1
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
