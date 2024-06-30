# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request


class ExportData(http.Controller):
    """ Controller class for exporting data from Odoo models."""
    @http.route('/get_data', auth="user", type='json')
    def get_export_data(self, **kw):
        """Controller method to fetch required details and export data.
        :param kw: Dictionary containing the following keys:
                   - fields: List of fields to export
                   - model: Name of the Odoo model
                   - res_ids: List of record IDs to export (optional)
                   - domain: Domain for record filtering (optional)
        :return: Dictionary containing exported data and column headers"""
        model = request.env[kw['model']]
        field_names = [field['name'] for field in kw['fields']]
        columns_headers = [val['label'].strip() for val in kw['fields']]
        domain = [('id', 'in', kw['res_ids'])] \
            if kw['res_ids'] else kw['domain']
        records = model.browse(kw['res_ids']) \
            if kw['res_ids'] \
            else model.search(domain, offset=0, limit=False, order=False)
        export_data = records.export_data(field_names).get('datas', [])
        return {'data': export_data, 'header': columns_headers}

    @http.route('/get_data/copy', auth="user", type='json')
    def get_export_data_copy(self, **kw):
        """Controller method to fetch required details, export data, and add
        column headers.
        :param kw: Dictionary containing the following keys:
                   - fields: List of fields to export
                   - model: Name of the Odoo model
                   - res_ids: List of record IDs to export (optional)
                   - domain: Domain for record filtering (optional)
        :return: List of lists containing exported data with column headers"""
        model = request.env[kw['model']]
        field_names = [field['name'] for field in kw['fields']]
        columns_headers = [val['label'].strip() for val in kw['fields']]
        domain = [('id', 'in', kw['res_ids'])] \
            if kw['res_ids'] else kw['domain']
        records = model.browse(kw['res_ids']) \
            if kw['res_ids'] \
            else model.search(domain, offset=0, limit=False, order=False)
        export_data = records.export_data(field_names).get('datas', [])
        export_data.insert(0, columns_headers)
        return export_data
