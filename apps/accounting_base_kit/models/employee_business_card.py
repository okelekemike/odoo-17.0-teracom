from odoo import fields, models, api

try:
    import qrcode
except ImportError:
    qrcode = None
try:
    import base64
except ImportError:
    base64 = None
from io import BytesIO


class EmployeeBusinessCard(models.Model):
    _inherit = "hr.employee"

    enable_business_card = fields.Boolean(string="Use Business Card", default=False, groups="hr.group_hr_user",
                                          help="Enable to use business card in employee profile and online.")
    gif = fields.Binary(groups="hr.group_hr_user", help="Personalized image on your business card")
    social_linkedin = fields.Char(string="Linkedin", groups="hr.group_hr_user", help="Linkedin Handle")
    social_facebook = fields.Char(string="Facebook",groups="hr.group_hr_user", help="Facebook Handle")
    social_instagram = fields.Char(string="Instagram",groups="hr.group_hr_user", help="Instagram Handle")
    url = fields.Char(string="Business Card URL", compute="_url", groups="hr.group_hr_user",
                      help="Link to your business card")
    bcFirstname = fields.Char(string="First Name", groups="hr.group_hr_user", help="First Name on Business Card")
    bcMiddlename = fields.Char(string="Middle Name", groups="hr.group_hr_user", help="Middle Name on Business Card")
    bcLastname = fields.Char(string="Last Name", groups="hr.group_hr_user", help="Last Name on Business Card")
    qr_code = fields.Binary("QR Code", compute='_generate_qr_code', groups="hr.group_hr_user",
                            help="QR Code link to your business card")
    address_qrcode = fields.Binary("Address QR Code", compute='_generate_address_qr_code', groups="hr.group_hr_user")

    @api.depends("url")
    def _generate_qr_code(self):
        for rec in self:
            if qrcode and base64:
                qr = qrcode.QRCode(version=1, box_size=10, border=4, error_correction=qrcode.constants.ERROR_CORRECT_L)
                qr.add_data(self.url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'qr_code': qr_image})

    @api.depends("enable_business_card")
    def _generate_address_qr_code(self):
        for rec in self:
            address_qr_code = """
            BEGIN:VCARD
                VERSION:3.0
                N;CHARSET=UTF-8:%(vcf_lastname)s;%(vcf_middlename)s;%(vcf_firstname)s
                FN;CHARSET=UTF-8:%(vcf_firstname)s %(vcf_middlename)s %(vcf_lastname)s
                TEL;WORK:%(vcf_phone)s
                ADR;CHARSET=UTF-8;WORK:;;%(vcf_street)s %(vcf_street2)s;%(vcf_city)s;%(vcf_state)s;%(vcf_zip)s;%(vcf_country)s
                EMAIL;WORK:%(vcf_email)s
                URL;WORK:%(vcf_website)s
                TITLE;CHARSET=UTF-8:%(vcf_job_title)s
                ORG;CHARSET=UTF-8:%(vcf_company_name)s
                NOTE: P.IVA: %(vcf_company_vat)s
            END:VCARD
            """ % dict(
                vcf_firstname=rec.bcFirstname or '',
                vcf_middlename=rec.bcMiddlename or '',
                vcf_lastname=rec.bcLastname or '',
                vcf_phone=rec.work_phone or '',
                vcf_street=rec.company_id.street or '',
                vcf_street2=rec.company_id.street2 or '',
                vcf_city=rec.company_id.city or '',
                vcf_state=rec.company_id.state_id.name or '',
                vcf_zip=rec.company_id.zip or '',
                vcf_country=rec.company_id.country_id.name or '',
                vcf_email=rec.work_email or '',
                vcf_website=rec.company_id.website or '',
                vcf_job_title=rec.job_title or '',
                vcf_company_name=rec.company_id.name or '',
                vcf_company_vat=rec.company_id.vat or '',
            )
            if qrcode and base64:
                qr = qrcode.QRCode(version=1, box_size=10, border=4, error_correction=qrcode.constants.ERROR_CORRECT_L)
                qr.add_data(address_qr_code)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                temp = BytesIO()
                img.save(temp, format="PNG")
                qr_image = base64.b64encode(temp.getvalue())
                rec.update({'address_qrcode': qr_image})

    def _url(self):
        for record in self:
            record.url = self.env['ir.config_parameter'].get_param('web.base.url').rstrip(
                '/') + "/business-card?employee=" + str(record.id)


class ResCompany(models.Model):
    _inherit = "res.company"

    bc_logo = fields.Binary()
    gif = fields.Binary()
