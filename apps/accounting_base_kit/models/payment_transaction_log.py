from odoo import models, fields


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    transaction_logs = fields.One2many("payment.transaction.log", "transaction_id")

    def register_log(self, level, summary, details=None,):
        """Create transaction logs
        Args:
            level (string): Type of logs to create (info, debug, warning, error, critical)
            summary (string): Summary of the log
            details (string): Data received or sent at the event. Defaults to None.

        Returns:
            record: Transaction log record
        """
        return self.env["payment.transaction.log"].create(
            {
                "transaction_id": self.id,
                "level": level,
                "summary": summary,
                "details": details,
            }
        )


class PaymentTransactionLog(models.Model):
    _name = "payment.transaction.log"
    _description = "Transaction Logs"

    transaction_id = fields.Many2one("payment.transaction")
    level = fields.Selection(
        selection=[
            ("debug", "DEBUG"),
            ("info", "INFO"),
            ("warning", "WARNING"),
            ("error", "ERROR"),
            ("critical", "CRITICAL"),
        ]
    )
    summary = fields.Char()
    details = fields.Text()
