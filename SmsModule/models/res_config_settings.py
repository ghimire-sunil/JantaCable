from odoo import api, fields, models, _

class setting(models.TransientModel):
    
    _inherit = 'res.config.settings'
    sms_token = fields.Char(string='Sms Token', config_parameter='src.sms_token',required=False)
