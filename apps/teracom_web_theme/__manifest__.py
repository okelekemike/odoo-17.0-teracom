{
    'name': 'Teracom Backend Theme',
    'summary': 'Odoo Community Backend Theme',
    'description': '''
        This module offers a mobile compatible design for Odoo Community. 
        Furthermore it allows the user to define some design preferences.
        So he can choose the size of the sidebar and the position of the 
        chatter. In addition, the background image of the app menu can be
        set for each company, quick product publish/Unpublish.
    ''',
    'version': '17.0.1.0.0',
    'category': 'Themes/Backend', 
    'license': 'LGPL-3', 
    'author': 'Teracom IT',
    'website': 'http://www.teracom.com',
    'live_test_url': 'https://teracom.com/demo',
    'contributors': [
        'Okeleke Mike <okelekemike@teracom.com>',
    ],
    'depends': [
        'base', 'mail', 'hr', 'contacts', 'website',
        'auth_signup', 'auth_password_policy_signup', 'product',
    ],
    'excludes': [
        'web_enterprise',
    ],
    'external_dependencies': {
        'python': ['dropbox', 'pyncclient', 'boto3', 'nextcloud-api-wrapper', 'paramiko', 'googletrans']
    },
    'data': [
        'views/signup_templates.xml',
        'templates/web_layout.xml',
        'data/ir_config_data.xml',
        'views/res_config_settings.xml',
        'views/product_views.xml',
        'data/employee_checklist_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_document_views.xml',
        'views/res_users.xml',
        'views/ir_actions_report.xml',
        'wizard/product_image_suggestion.xml',
        'security/ir.model.access.csv',
        'security/res_users_pass_history.xml',
        # Automatic Database Backup
        'data/mail_template_data.xml',
        'views/db_backup_configure_views.xml',
        'wizard/dropbox_auth_code_views.xml',
        # Partner Search By Number
        'views/res_partner_views.xml',
        # Reports With Watermark
        'views/res_company_views.xml',
        'views/pdf_with_watermark_template.xml',
        # Scroll Button In Website
        'views/website_scroll_buttons_templates.xml',
        # Bulk Password Update
        'views/bulk_password_user.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'teracom_web_theme/static/src/scss/colors_light.scss'),
            (
                'after',
                'teracom_web_theme/static/src/scss/colors_light.scss',
                'teracom_web_theme/static/src/scss/colors.scss'
            ),
            (
                'after',
                'web/static/src/scss/primary_variables.scss',
                'teracom_web_theme/static/src/scss/variables.scss'
            ),
        ],
        'web.dark_mode_variables': [
            (
                'after',
                'teracom_web_theme/static/src/scss/colors_light.scss',
                'teracom_web_theme/static/src/scss/colors_dark.scss'
            ),
        ],
        'web._assets_backend_helpers': [
            'teracom_web_theme/static/src/scss/mixins.scss',
        ],
        'web.assets_backend': [
            (
                'after',
                'web/static/src/webclient/navbar/navbar.xml',
                'teracom_web_theme/static/src/webclient/navbar/navbar.xml',
            ),
            (
                'after',
                'web/static/src/webclient/navbar/navbar.js',
                'teracom_web_theme/static/src/webclient/navbar/navbar.js',
            ),
            (
                'after',
                'mail/static/src/views/web/form/form_compiler.js',
                'teracom_web_theme/static/src/views/form/form_compiler.js'
            ),
            ('include', 'web_editor.assets_wysiwyg'),
            'teracom_web_theme/static/src/webclient/**/*.xml',
            'teracom_web_theme/static/src/webclient/**/*.scss',
            'teracom_web_theme/static/src/webclient/**/*.css',
            'teracom_web_theme/static/src/webclient/**/*.js',
            'teracom_web_theme/static/src/views/**/*.scss',
            'teracom_web_theme/static/src/core/**/*.xml',
            'teracom_web_theme/static/src/core/**/*.scss',
            'teracom_web_theme/static/src/css/ent_web_asset_backend.css',
        ],
        'web.assets_frontend': [
            'teracom_web_theme/static/src/css/web_asset_frontend.css',
            'teracom_web_theme/static/src/core/website_scroll_buttons/*.css',
            'teracom_web_theme/static/src/core/website_scroll_buttons/*.js',
        ],
        'point_of_sale._assets_pos': [
            'teracom_web_theme/static/src/css/point_of_sale_asset.css',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '_setup_module',
    'uninstall_hook': '_uninstall_cleanup',
}
