import nepali_datetime
import datetime
from ..tools.automation import VCTSAutomation
import time
import random
from odoo import models, fields, _


def unique_number():
    timestamp = int(time.time() * 1000)
    random_part = random.randint(100, 999)
    return int(f"{timestamp}{random_part}")


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    vcts_url = fields.Char(
        string="VCTS Domain",
        default="https://vctsdri.dri.gov.np/",
        config_parameter="vstcs.url",
    )
    vcts_username = fields.Char(
        string="VCTS Email",
        help="Login Email of https://vctsdri.dri.gov.np/",
        config_parameter="vstcs.username",
    )
    vcts_password = fields.Char(
        string="VCTS Password", config_parameter="vstcs.password"
    )

    def test_selenium(self):
        try:
            vcts = VCTSAutomation(env=self.env, sale=None, shippingInfo={})
            vcts.test_automation()

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("VCTS automation test completed successfully."),
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Error"),
                    "message": _("Error: %s" % str(e)),
                    "type": "danger",
                    "sticky": True,
                },
            }
