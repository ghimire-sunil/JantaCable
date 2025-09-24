from odoo import models, fields


class CRMImage(models.Model):
    _name = "crm.image"
    _description = "CRM Image"
    _inherit = ["image.mixin"]
    _order = "sequence, id"

    name = fields.Char(string="Name", required=True)
    sequence = fields.Integer(default=10)

    image_1920 = fields.Binary()

    crm_id = fields.Many2one(
        string="CRM Lead",
        comodel_name="crm.lead",
        ondelete="cascade",
        index=True,
    )


class CRMLeadInherited(models.Model):
    _inherit = "crm.lead"

    crm_image_ids = fields.One2many(
        string="CRM Media",
        comodel_name="crm.image",
        inverse_name="crm_id",
        copy=True,
    )


class CRMTeam(models.Model):
    _inherit = "crm.team"

    default_distributor_id = fields.Many2one(
        "res.partner", string="Default Distributor"
    )

    member_ids = fields.Many2many(
        "res.users",
        string="Salespersons",
        domain="[('company_ids', 'in', member_company_ids)]",
        compute="_compute_member_ids",
        inverse="_inverse_member_ids",
        search="_search_member_ids",
        help="Users assigned to this team.",
    )
