from datetime import datetime
from odoo import fields, models, api
from odoo.exceptions import UserError


DISTRIBUTER_ORDER_STATE = [
    ("draft", "Draft"),
    ("pending", "Pending"),
    ("assigned", "Assigned"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]

DELIVERY_STATE = [
    ("pending", "Pending"),
    ("completed", "Completed"),
    ("cancelled", "Cancelled"),
]


class DistributorOrder(models.Model):
    _name = "distributor.order"
    _description = "Distributor Order"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]

    name = fields.Char(
        string="Order Reference",
        required=True,
        copy=False,
        readonly=False,
        index="trigram",
        default=lambda self: "New",
    )
    partner_id = fields.Many2one("res.partner", "Customer", required=True)

    order_date = fields.Date("Order Date")
    state = fields.Selection(DISTRIBUTER_ORDER_STATE, default="draft", tracking=True)
    delivery_status = fields.Selection(DELIVERY_STATE, default="pending")
    order_line_ids = fields.One2many("distributor.order.line", inverse_name="order_id")
    user_id = fields.Many2one(comodel_name="res.users", string="Salesperson")

    distributor_id = fields.Many2one(
        "res.partner", domain="[('id','in',allowed_distributor_ids)]"
    )

    crm_team_id = fields.Many2one(
        comodel_name="crm.team",
        string="Crm Team",
        compute="_compute_sales_team",
        store=True,
    )

    allowed_distributor_ids = fields.One2many(
        comodel_name="res.partner", compute="_compute_allowed_team"
    )

    def unlink(self):
        for rec in self:
            if rec.state not in ["cancelled", "draft"]:
                raise UserError("You can only delete draft or pending orders !!")
        return super().unlink()

    # business methods
    def action_confirm(self):
        for rec in self:
            rec._action_confirm()

    def action_draft(self):
        for rec in self:
            rec._action_draft()

    def action_cancel(self):
        for rec in self:
            rec._action_cancel()

    def action_assign(self):
        for rec in self:
            rec._action_assigned()

    def action_complete(self):
        for rec in self:
            rec._action_complete()

    def _action_cancel(self):
        self.write({"state": "cancelled"})

    def _action_confirm(self):
        if self.name == "New":
            self.name = (
                self.env["ir.sequence"].next_by_code("distributor_order.order") or "New"
            )
        self.write({"state": "pending", "order_date": datetime.now()})

    def _action_draft(self):
        self.write({"state": "draft"})

    def _action_assigned(self):
        if not self.distributor_id:
            raise UserError("Please select distributor!!")
        self.write({"state": "assigned"})

    def _action_complete(self):
        self.write({"state": "completed"})

    @api.depends("distributor_id")
    def _compute_sales_team(self):
        for rec in self:
            if rec.distributor_id.sales_team_ids:
                rec.crm_team_id = rec.distributor_id.sales_team_ids[0].id
            else:
                rec.crm_team_id = False

    @api.depends("user_id")
    def _compute_allowed_team(self):
        for rec in self:
            rec.allowed_distributor_ids = False

            print(rec.user_id.crm_team_ids)
            rec.allowed_distributor_ids = (
                rec.user_id.crm_team_ids.default_distributor_id.ids
            )


class DistributorOrderLine(models.Model):
    _name = "distributor.order.line"
    _description = "Distributor Orderline"

    order_id = fields.Many2one("distributor.order")
    product_id = fields.Many2one("product.product")
    uom_id = fields.Many2one(related="product_id.uom_id")
    qty = fields.Float("Quantity")
    delivered_qty = fields.Float("Delivered")
    delivery_status = fields.Selection(
        DELIVERY_STATE, related="order_id.delivery_status"
    )       
