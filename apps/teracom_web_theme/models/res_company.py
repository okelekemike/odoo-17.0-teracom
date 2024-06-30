from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    # ----------------------------------------------------------
    # Fields
    # ----------------------------------------------------------

    favicon = fields.Binary(
        string="Company Favicon",
        attachment=True
    )

    background_image = fields.Binary(
        string='Apps Menu Background',
        attachment=True
    )

    appbar_image = fields.Binary(
        string='Apps Menu Footer Image',
        attachment=True
    )


    # ----------------------------------------------------------
    # Introduce watermark in pdf reports
    # ----------------------------------------------------------

    watermark = fields.Boolean(
        string='Watermark',
        help='Enable it, if you want to apply watermark on all your pdf reports')
    content_text = fields.Char(
        string='Text',
        help="Enter the text You want to display")
    watermark_type = fields.Selection([('image', 'Image'),
                                       ('text', 'Text'),
                                       ('logo', 'Logo'), ],
                                      default='text',
                                      help='Select the Type of watermark')
    color_picker = fields.Char(string='Color Picker', help='Select the Color')
    font_size = fields.Integer(string='Font size', default=20,
                               help="Enter the font size for the text")
    pdf_background_image = fields.Image(string='Image',
                                        help='Set an image to display')
    rotating_angle = fields.Float(string='Angle of Rotation',
                                  help='Enter the angle of rotation')

    avoid_products_name_duplication = fields.Boolean(
        string='Restrict Products Name Duplication',
        help='If checked, avoid duplicate products names within.'
    )
    avoid_internal_references_duplication = fields.Boolean(
        string='Restrict Products Internal Reference Duplication',
        help='If checked, avoid duplicate products reference within.'
    )


class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    watermark = fields.Boolean(related='company_id.watermark', readonly=False)
    content_text = fields.Char(related='company_id.content_text', readonly=False)
    watermark_type = fields.Selection(related='company_id.watermark_type', readonly=False)
    color_picker = fields.Char(related='company_id.color_picker', readonly=False)
    font_size = fields.Integer(related='company_id.font_size', readonly=False)
    pdf_background_image = fields.Image(related='company_id.pdf_background_image', readonly=False)
    rotating_angle = fields.Float(related='company_id.rotating_angle', readonly=False)
