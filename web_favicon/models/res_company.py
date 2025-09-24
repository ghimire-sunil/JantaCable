import hashlib
from odoo import api, fields, models
from odoo.http import request


class ResCompany(models.Model):
    _inherit = "res.company"

    def _get_default_favicon(self):
        return self.logo

    favicon = fields.Binary(
        string="Company Favicon",
        help="This field holds the image used to display favicon for a given company.",
        related="partner_id.image_1920",
    )

    @api.model_create_multi
    def create(self, vals_list):
        # add default favicon
        for vals in vals_list:
            if not vals.get("favicon"):
                vals["favicon"] = self._get_default_favicon()
        return super().create(vals_list)

    # Get favicon from current company
    @api.model
    def _get_favicon(self):
        """Returns a local url that points to the image field of a given record."""
        if self.env.context.get("website_id"):
            website = self.env["website"].browse(self.env.context.get("website_id"))
            return website.image_url(website, "favicon")
        company_id = (
            request.httprequest.cookies.get("cids")
            if request.httprequest.cookies.get("cids")
            else False
        )
        company = (
            self.browse(int(company_id.split("-")[0])).sudo()
            if company_id and self.browse(int(company_id.split("-")[0])).sudo().favicon
            else False
        )
        if company:
            sha = hashlib.sha512(str(company.write_date).encode("utf-8")).hexdigest()[
                :7
            ]
            return f"/web/image/{self._name}/{company.id}/favicon?unique={sha}"
        else:
            return False
