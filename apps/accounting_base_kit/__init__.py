# -*- coding: utf-8 -*-

from . import controllers
from . import models
from . import report
from . import wizard


def post_init_hook(env):
    env.cr.execute(
        """
        UPDATE account_bank_statement_line
        SET reconcile_mode = 'edit'
        WHERE is_reconciled
        """
    )

