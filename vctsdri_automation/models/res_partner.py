import re
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    license_number = fields.Char(string="License Number")
    district_id = fields.Many2one(
        string="District",
        comodel_name="res.district",
    )

    @api.constrains("license_number")
    def _check_license_number(self):
        for record in self:
            if record.license_number:
                if not re.fullmatch(r"[0-9\-]+", record.license_number):
                    raise ValidationError(
                        _("License number can only contain digits and dashes.")
                    )
