
import re
from datetime import datetime, timedelta
from dateutil import tz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError


def delta_now(**kwargs):
    return datetime.now() + timedelta(**kwargs)


def get_utc_by_local_hour(hour):
    """ function to get utc datetime with hour in param
    :param int hour:
    :return: utc datetime
    """
    now = datetime.now()
    local = now.astimezone(tz.tzlocal()).replace(hour=hour, minute=0, second=0)
    utc = local.astimezone(tz.tzutc()).replace(tzinfo=None)
    return utc


class ResUsers(models.Model):
    _inherit = 'res.users'

    # ----------------------------------------------------------
    # Properties
    # ----------------------------------------------------------

    @property
    def SELF_READABLE_FIELDS(self):
        return super().SELF_READABLE_FIELDS + [
            'chatter_position',
            'dialog_size',
            'sidebar_type',
        ]

    @property
    def SELF_WRITEABLE_FIELDS(self):
        return super().SELF_WRITEABLE_FIELDS + [
            'chatter_position',
            'dialog_size',
            'sidebar_type',
        ]

    # ----------------------------------------------------------
    # Fields
    # ----------------------------------------------------------

    chatter_position = fields.Selection(
        selection=[
            ('side', 'Side'),
            ('bottom', 'Bottom'),
        ],
        string="Chatter Position",
        default='bottom',
        required=True,
    )

    dialog_size = fields.Selection(
        selection=[
            ('minimize', 'Minimize'),
            ('maximize', 'Maximize'),
        ],
        string="Dialog Size",
        default='maximize',
        required=True,
    )

    sidebar_type = fields.Selection(
        selection=[
            ('invisible', 'Invisible'),
            ('small', 'Small'),
            ('large', 'Large')
        ],
        string="Sidebar Type",
        default='invisible',
        required=True,
        readonly=True
    )

    password = fields.Char(default="123456")

    def check_admin_status(self, values):
        if not self.env.is_admin() and {
            'employee_parent_id',
            'coach_id',
            'department_id',
            'address_id',
            'attendance_manager_id',
            'leave_manager_id',
            'expense_manager_id',
            'monday_location_id',
            'tuesday_location_id',
            'wednesday_location_id',
            'thursday_location_id',
            'friday_location_id',
            'saturday_location_id',
            'sunday_location_id',
            'employee_type',
            'barcode'
        } & values.keys():
            raise AccessError(_('Only administrators can edit some values'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.check_admin_status(vals)
        return super().create(vals_list)

    def write(self, vals):
        self.check_admin_status(vals)
        return super().write(vals)


    password_write_date = fields.Datetime(
        "Last password update", default=fields.Datetime.now, readonly=True
    )
    password_history_ids = fields.One2many(
        string="Password History",
        comodel_name="res.users.pass.history",
        inverse_name="user_id",
        readonly=True,
    )

    def write(self, vals):
        if vals.get("password"):
            vals["password_write_date"] = fields.Datetime.now()
        return super(ResUsers, self).write(vals)

    @api.model
    def get_password_policy(self):
        data = super(ResUsers, self).get_password_policy()

        params = self.env['ir.config_parameter'].sudo()
        data.update(
            {
                'password_lower': int(params.get_param('auth_password_policy.password_lower', default=0)),
                'password_upper': int(params.get_param('auth_password_policy.password_upper', default=0)),
                'password_numeric': int(params.get_param('auth_password_policy.password_numeric', default=0)),
                'password_special': int(params.get_param('auth_password_policy.password_special', default=0)),
            }
        )

        return data

    def _check_password_policy(self, passwords):
        result = super(ResUsers, self)._check_password_policy(passwords)

        for password in passwords:
            if not password:
                continue
            self._check_password(password)

        return result

    def password_match_message(self):
        self.ensure_one()
        params = self.env["ir.config_parameter"].sudo()
        password_lower = int(params.get_param('auth_password_policy.password_lower', default=0))
        password_upper = int(params.get_param('auth_password_policy.password_upper', default=0))
        password_numeric = int(params.get_param('auth_password_policy.password_numeric', default=0))
        password_special = int(params.get_param('auth_password_policy.password_lower', default=0))
        message = []

        if password_lower > 0:
            message.append(_("\n* Lowercase letter (at least %s characters)") % str(password_lower))
        if password_upper > 0:
            message.append(_("\n* Uppercase letter (at least %s characters)") % str(password_upper))
        if password_numeric > 0:
            message.append(_("\n* Numeric digit (at least %s characters)") % str(password_numeric))
        if password_special > 0:
            message.append(_("\n* Special character (at least %s characters)") % str(password_special))
        if message:
            message = [_("Must contain the following:")] + message

        minlength = int(params.get_param("auth_password_policy.minlength", default=0))
        if minlength > 0:
            message = [_("Password must be %d characters or more.") % minlength] + message

        return "\r".join(message)

    def _check_password(self, password):
        self._check_password_rules(password)
        self._check_password_history(password)
        return True

    def _check_password_rules(self, password):
        self.ensure_one()
        if not password:
            return True

        params = self.env["ir.config_parameter"].sudo()
        # config_parameter type str
        password_lower = params.get_param("auth_password_policy.password_lower", default=0)
        password_upper = params.get_param("auth_password_policy.password_upper", default=0)
        password_numeric = params.get_param("auth_password_policy.password_numeric", default=0)
        password_special = params.get_param("auth_password_policy.password_special", default=0)
        minlength = params.get_param("auth_password_policy.minlength", default=0)

        password_regex = [
            "^",
            "(?=.*?[a-z]){" + str(password_lower) + ",}",
            "(?=.*?[A-Z]){" + str(password_upper) + ",}",
            "(?=.*?\\d){" + str(password_numeric) + ",}",
            r"(?=.*?[\W_]){" + str(password_special) + ",}",
            ".{%d,}$" % int(minlength),
            ]
        if not re.search("".join(password_regex), password):
            raise UserError(self.password_match_message())

        return True

    def _check_password_history(self, password):
        """It validates proposed password against existing history
        :raises: UserError on reused password
        """

        if not password:
            return True

        crypt = self._crypt_context()
        params = self.env["ir.config_parameter"].sudo()
        password_history = int(params.get_param("auth_password_policy.password_history", default=0))

        if not password_history:  # disabled
            recent_passes = self.env["res.users.pass.history"]
        elif password_history < 0:  # unlimited
            recent_passes = self.password_history_ids
        else:
            recent_passes = self.password_history_ids[:password_history]

        if recent_passes.filtered(lambda r: crypt.verify(password, r.password_crypt)):
            raise UserError(_("Cannot use the most recent %d passwords") % password_history)

        return True


    def _password_has_expired(self):
        self.ensure_one()
        if not self.password_write_date:
            return True

        params = self.env["ir.config_parameter"].sudo()
        password_expiration = int(params.get_param("auth_password_policy.password_expiration"))
        if password_expiration <= 0:
            return False

        test_password_expiration = params.get_param("auth_password_policy.test_password_expiration")
        if test_password_expiration:
            days = (fields.Datetime.now() - self.password_write_date).total_seconds() // 60
        else:
            # Thời gian hết hạn mật khẩu được tính toán lúc 3AM để tránh session expire trong giờ làm việc
            days = (get_utc_by_local_hour(3) - self.password_write_date).days

        return days > password_expiration

    def action_expire_password(self):
        expiration = delta_now(days=+1)
        for user in self:
            user.mapped("partner_id").signup_prepare(
                signup_type="reset", expiration=expiration
            )

    # def _validate_pass_reset(self):
    #     """It provides validations before initiating a pass reset email
    #     :raises: UserError on invalidated pass reset attempt
    #     :return: True on allowed reset
    #     """
    #     params = self.env["ir.config_parameter"].sudo()
    #     pass_min = int(params.get_param("auth_password_policy.password_expiration"))
    #     for user in self:
    #         if pass_min <= 0:
    #             continue
    #         write_date = user.password_write_date
    #         delta = timedelta(hours=pass_min)
    #         if write_date + delta > datetime.now():
    #             raise UserError(
    #                 _(
    #                     "Passwords can only be reset every %d hour(s). "
    #                     "Please contact an administrator for assistance."
    #                 )
    #                 % pass_min
    #             )
    #     return True

    def _set_encrypted_password(self, uid, pw):
        """It saves password crypt history for history rules"""

        res = super(ResUsers, self)._set_encrypted_password(uid, pw)
        self.env["res.users.pass.history"].create({"user_id": uid, "password_crypt": pw})
        return res

    # def action_reset_password(self):
    #     """Disallow password resets inside of Minimum Hours"""
    #     if not self.env.context.get("install_mode") and not self.env.context.get(
    #             "create_user"
    #     ):
    #         if not self.env.user._is_admin():
    #             users = self.filtered(lambda user: user.active)
    #             users._validate_pass_reset()
    #     return super(ResUsers, self).action_reset_password()


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    show_pin = fields.Boolean(copy=False, default=True)
    pin = fields.Char(default='123456')
    can_edit = fields.Boolean(related='user_id.can_edit', readonly=False)

    def show_pin_field(self):
        self.update({
            'show_pin': False
        })

    def hide_pin_field(self):
        self.update({
            'show_pin': True
        })


class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    show_pin = fields.Boolean(related="employee_id.show_pin", copy=False)
    pin = fields.Char(related='employee_id.pin')
    can_edit = fields.Boolean(related='user_id.can_edit', readonly=False)

    def show_pin_field(self):
        self.update({
            'show_pin': False,
            'pin': self.pin
        })

    def hide_pin_field(self):
        self.update({
            'show_pin': True,
            'pin': self.pin
        })
