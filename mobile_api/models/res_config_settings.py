from odoo import api, fields, models, _

class SettingInherited(models.TransientModel):
    _inherit = 'res.config.settings'

    manual_payment = fields.Boolean(string='Manual Payment', config_parameter = 'mobile_api.manual_payment', store=True)
