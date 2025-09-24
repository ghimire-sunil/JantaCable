from odoo import fields, models

class AttendanceInherited(models.Model):
    _inherit = 'hr.attendance'

    image_1920 = fields.Image()