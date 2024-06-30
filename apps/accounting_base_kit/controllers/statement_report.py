""" controller for xlsx report """
# -*- coding: utf-8 -*-

import json
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools import html_escape


class XLSXReportController(http.Controller):
    """ controller for xlsx report """
    @http.route('/xlsx_report', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, model, data, output_format, report_name):
        """Generate an XLSX report based on the provided data and return it as
        a response.
            Args:
                model (str): The name of the model on which the report is based.
                data (str): The data required for generating the report.
                output_format (str): The desired output format for the report
                (e.g., 'xlsx').
                report_name (str): The name to be given to the generated report
                file.
            Returns:
                Response: The generated report file as a response.
            Raises:
                Exception: If an error occurs during report generation.
            """
        uid = request.session.uid
        report_obj = request.env[model].with_user(uid)
        token = 'dummy-because-api-expects-one'
        data = json.loads(data)
        try:
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition',
                         content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(data, response, report_name)
                response.set_cookie('fileToken', token)
                return response
        except Exception as event:
            serialize = http.serialize_exception(event)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': serialize
            }
            return request.make_response(html_escape(json.dumps(error)))
