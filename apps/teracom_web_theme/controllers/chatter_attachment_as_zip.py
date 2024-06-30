# -*- coding: utf-8 -*-

import base64
import io
import zipfile
from odoo import http
from odoo.http import request


class DownloadAllAttachments(http.Controller):
    """Controller for downloading all attachments as a single zip file"""
    @http.route('/chatter/attachments/download/zip', type='http', auth="public", cors="*", csrf=False)
    def download_attachments(self, **res_id):
        """
            Download all attachments as a single zip file.
            Args:
                res_id (dict): A dictionary containing the 'res_id' parameter.
            Returns:
                werkzeug.wrappers.Response: HTTP response with the zip file.
            """
        chatter_id = request.params.get('res_id')
        attachments = request.env['ir.attachment'].search(
            [('res_id', '=', chatter_id), ('res_model', '!=', 'account.move')])
        if attachments:
            # Define the name of the zip file
            zip_filename = f'attachments_{chatter_id}.zip'
            # Create a zip file with the attachments and prepare it for download
            zip_data = io.BytesIO()
            with zipfile.ZipFile(zip_data, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for attachment in attachments:
                    # Decode binary data using base64 library
                    attachment_data = base64.b64decode(attachment.datas)
                    zipf.writestr(attachment.name, attachment_data)
            # Prepare HTTP response with the zip file
            response = request.make_response(
                zip_data.getvalue(),
                headers=[
                    ('Content-Type', 'application/zip'),
                    ('Content-Disposition',
                     f'attachment; filename={zip_filename}'),
                ]
            )
            zip_data.close()
            return response
