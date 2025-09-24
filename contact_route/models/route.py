from odoo import api, fields, models
from datetime import date, timedelta


class Route(models.Model):
    _name = "delivery.route"
    _inherit = ["mail.thread"]

    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        tracking=True,
        required=True,
    )
    state_id = fields.Many2one(
        comodel_name="res.country.state", string="State", tracking=True, required=True
    )
    next_delivery_schedule = fields.Date(
        string="Next Delivery Schedule", compute="_compute_next_delivery_schedule"
    )

    delivery_schedules = fields.One2many(
        string="Delivery Schedules",
        comodel_name="delivery.route.schedule",
        inverse_name="route_id",
    )

    def _compute_next_delivery_schedule(self):
        for record in self:
            schedule_date = record.delivery_schedules.filtered(
                lambda r: r.next_delivery_schedule
            ).sorted(key=lambda r: r.next_delivery_schedule)
            if schedule_date:
                record.next_delivery_schedule = schedule_date[0].next_delivery_schedule
            else:
                record.next_delivery_schedule = None


class RouteSchedule(models.Model):
    _name = "delivery.route.schedule"

    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        required=True,
    )
    route_id = fields.Many2one(
        string="Route",
        comodel_name="delivery.route",
        required=True,
    )

    delivery_schedule_day = fields.Selection(
        string="Delivery Schedule Day",
        selection=[
            ("sunday", "Sunday"),
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
            ("saturday", "Saturday"),
        ],
        required=True,
    )
    next_delivery_schedule = fields.Date(
        string="Next Delivery Schedule", compute="_compute_next_delivery_schedule"
    )

    @api.depends("delivery_schedule_day")
    def _compute_next_delivery_schedule(self):
        today = date.today()

        weekday_map = {
            "monday": 0,
            "tuesday": 1,
            "wednesday": 2,
            "thursday": 3,
            "friday": 4,
            "saturday": 5,
            "sunday": 6,
        }

        today_weekday_num = today.weekday()

        for record in self:
            if record.delivery_schedule_day:
                target_weekday_num = weekday_map[record.delivery_schedule_day]
                days_until_next = (target_weekday_num - today_weekday_num + 7) % 7
                if days_until_next == 0:
                    days_until_next = 7

                next_target_date = today + timedelta(days=days_until_next)

                record.next_delivery_schedule = next_target_date
            else:
                record.next_delivery_schedule = None
