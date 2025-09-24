import requests
from odoo.exceptions import UserError

from odoo import fields, models


class Setting(models.TransientModel):
    _inherit = "res.config.settings"

    traccar_token = fields.Char(
        string="Traccar Token", config_parameter="traccar.token", required=False
    )
    url = fields.Char(string="API URL", config_parameter="traccar.url", required=False)
    traccar_username = fields.Char(
        "Userame", config_parameter="traccar.username", required=False
    )
    traccar_password = fields.Char(
        "Password", config_parameter="traccar.password", required=False
    )
