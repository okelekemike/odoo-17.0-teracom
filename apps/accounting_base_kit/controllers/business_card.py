from odoo import http
from odoo.http import request, route, NotFound

class BusinessCard(http.Controller):
    @http.route('/business-card', auth='public', website="True")
    def show_business_card(self, **kwargs ):
        employee_id = kwargs.get('employee')
        if employee_id:
            employee_data = request.env["hr.employee"].sudo().search([('id','=',employee_id)])
            if employee_data:
                employee_data = employee_data[0]
                values = {
                    'employee_data': employee_data
                } 
                if employee_data.enable_business_card:
                    return request.render('accounting_base_kit.business_card', values)
        raise NotFound()