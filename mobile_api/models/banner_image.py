from odoo import api, fields, models
from datetime import date


class BannerImage(models.Model):
    _name = "banner.image"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]

    name = fields.Char()
    image_1920 = fields.Image(string="Image", default="New", required=True)
    url = fields.Char(string="URL", compute="_compute_url", default="")
    published = fields.Boolean(string="Published")
    sequence = fields.Integer(string="Sequence")
    start_date = fields.Date(string="Date From", required=True, default=date.today())
    end_date = fields.Date(string="Date To", required=True, default=date.today())

    @api.depends("image_1920")
    def _compute_url(self):
        for record in self:
            record.url = f"/web/image/banner.image/{record.id}/image_1920"

    def create(self, vals):
        res = super().create(vals)
        res.name = self.env["ir.sequence"].next_by_code("banner.images") or "New"
        return res
