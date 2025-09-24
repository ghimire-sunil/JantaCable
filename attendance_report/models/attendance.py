from datetime import date, datetime, timedelta, time
from odoo.exceptions import UserError
import nepali_datetime
import pandas as pd
from odoo import models, fields, api, exceptions, _
from odoo.tools import format_datetime
import pytz
import calendar
import logging

_logger = logging.getLogger(__name__)


class resourceCalenderLeave(models.Model):
    _inherit = "resource.calendar.leaves"

    date = fields.Date("Date", compute="_compute_date", store=True, index=True)
    in_use = fields.Boolean()

    def _compute_date(self):
        for rec in self:
            rec.date = rec.date_from


class AttendanceReport(models.AbstractModel):
    _name = "report.attendance_report.filter_records"

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["attendance.filter"].browse(docids)
        # if not docs:
        #     raise ValueError("No records found for the provided docids.")

        extra = docs[0].get_attendance_data()
        # if not extra:
        #     raise ValueError("No attendance data found.")

        return {
            "doc_ids": docids,
            "doc_model": "attendance.filter",
            "docs": docs,
            "data": data,
            "extra": extra,
        }


class AttendanceFilter(models.TransientModel):
    _name = "attendance.filter"
    _rec_name = "name"

    name = fields.Char(
        string="Attendance Report",
        help="Name",
        readonly=True,
        default="Attendance Report",
    )
    from_date = fields.Date("From", required=True, store=True)
    to_date = fields.Date("To", required=True, default=date.today(), store=True)
    employee_ids = fields.Many2many("hr.employee", string="Employees")
    date_range = fields.Char(string="Date Range", compute="_compute_date_range")
    department_id = fields.Many2one("hr.department", string="Department", store=True)

    @api.onchange("department_id")
    def _onchange_department_id(self):
        if self.department_id:
            self.employee_ids = self.department_id.member_ids

    @api.depends("from_date", "to_date")
    def _compute_date_range(self):
        for rec in self:
            if rec.from_date and rec.to_date:
                date_range = pd.date_range(
                    start=rec.from_date, end=rec.to_date
                ).strftime("%Y-%m-%d")
                # date_in = datetime.strptime(date_in_str, '%Y-%m-%d').date()
                # Convert the date range to a comma-separated string
                rec.date_range = ", ".join(date_range)

                print(rec.date_range, "join")
            else:
                # If either 'date' or 'to' is empty, set 'date_range' to an empty string
                self.date_range = ""

    def action_print_report(self):
        return self.env.ref(
            "attendance_report.action_record_attendance_department"
        ).report_action(self)

    def get_excel_report(self):
        """
        Redirect to the controller to generate the Excel file.
        """
        return {
            "type": "ir.actions.act_url",
            "url": f"/attendance/excel_report/{self.id}",
            "target": "new",
        }

    def get_attendance_data(self):
        for rec in self:
            # Check if there is a specific employee record
            employees = rec.employee_ids
            # If no specific employee record, fetch all the employees from department
            if not rec.employee_ids:
                employees = rec.department_id.member_ids

            attendance_data = []
            total = (self.to_date - self.from_date).days + 1

            for employee_id in employees:
                total_present = 0
                total_weekend = 0
                total_absent = 0
                total_leave = 0
                total_holiday = 0
                records = []

                for date_in_str in self.date_range.split(", "):
                    # Convert the date string to a datetime object with time 00:00:00
                    date_in = datetime.strptime(date_in_str, "%Y-%m-%d").date()
                    date_in_from = datetime.combine(date_in, time.min)
                    date_in_to = datetime.combine(date_in, time.max)

                    # Search for attendance record for the employee on the specific date
                    record = (
                        self.env["hr.attendance"]
                        .sudo()
                        .search_read(
                            domain=[
                                ("employee_id", "=", employee_id.id),
                                ("date", "=", date_in),
                            ],
                            limit=1,
                        )
                    )

                    leave = self.env["hr.leave"].search(
                        [
                            ("employee_id", "=", employee_id.id),
                            ("request_date_from", "<=", date_in),
                            ("request_date_to", ">=", date_in),
                            ("state", "=", "validate"),
                        ],
                        limit=1,
                    )
                    public_holiday = self.env["resource.calendar.leaves"].search(
                        [
                            ("date_from", "<=", date_in_to),
                            ("date_to", ">=", date_in_from),
                            ("in_use", "=", True),
                            ("calendar_id", "=", employee_id.resource_calendar_id.id),
                        ]
                    )
                    if record:
                        record[0]["date"] = nepali_datetime.date.from_datetime_date(
                            record[0]["date"]
                        )
                        if record[0]["check_in"]:
                            record[0]["check_in"] = record[0]["check_in"] + timedelta(
                                hours=5, minutes=45
                            )

                        if record[0]["check_out"]:
                            record[0]["check_out"] = record[0]["check_out"] + timedelta(
                                hours=5, minutes=45
                            )

                        records.append(record[0])
                        if record[0]["remarks"] == "Present":
                            total_present += 1

                    else:
                        if employee_id.resource_calendar_id:
                            day_of_week = str(date_in.weekday())
                            is_working_day = False
                            for a in employee_id.resource_calendar_id.attendance_ids:
                                if a.dayofweek == day_of_week:
                                    is_working_day = True
                                    break

                            if is_working_day:
                                if leave:
                                    remarks = f"({leave.holiday_status_id.name})"
                                    total_leave += 1
                                elif public_holiday:
                                    remarks = f"{public_holiday.name}"
                                    total_holiday += 1
                                else:
                                    remarks = "Absent"
                                    total_absent += 1
                            else:
                                if public_holiday and not is_working_day:
                                    remarks = public_holiday.name
                                    total_holiday += 1
                                else:
                                    remarks = "Weekend"
                                    total_weekend += 1

                        records.append(
                            {
                                "date": nepali_datetime.date.from_datetime_date(
                                    date_in
                                ),
                                "day": pd.to_datetime(date_in).strftime("%A"),
                                "check_in": False,
                                "check_out": False,
                                "worked_hours": False,
                                "employee_id": [employee_id.id, employee_id.name],
                                "remarks": remarks,
                            }
                        )

                recorded_data = self.env["hr.attendance"].search_count(
                    [
                        ("employee_id", "=", employee_id.id),
                        ("date", ">=", self.from_date),
                        ("date", "<=", self.to_date),
                    ]
                )

                if recorded_data != 0:
                    attendance_data.append(
                        {
                            "employee_id": employee_id.name,
                            "records": records,
                            "total_present": total_present,
                            "total_weekend": total_weekend,
                            "total_absent": total_absent,
                            "total_leave": total_leave,
                            "total_holiday": total_holiday,
                            "recorded_data": recorded_data,
                        }
                    )

            if attendance_data:
                return {
                    "form_data": self.read()[0],
                    "attendance_data": attendance_data,
                    "total": total,
                    "form": {
                        "date_range": self.date_range.split(", "),
                        "from_date": nepali_datetime.date.from_datetime_date(
                            self.from_date
                        ),
                        "to_date": nepali_datetime.date.from_datetime_date(
                            self.to_date
                        ),
                        "department": self.department_id.name,
                    },
                }
            else:
                raise UserError("Failed! Sorry, no data found!")

    def get_file_name(self):
        return f"Attendance-{self.from_date} to {self.to_date}"


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _order = "date"
    #
    # late_in_hrs = fields.Float(
    #     string='Late In Hours', compute="_compute_late_in_hours", store=True, default=False, readonly=True)
    # early_out_hrs = fields.Float(string='Early Out Hours', store=True,
    #                              compute="_compute_early_out_hours", default=False, readonly=True)
    # break_in = fields.Datetime(
    #     string='Break in time', store=True, default=False)
    # break_out = fields.Datetime(
    #     string='Break out time', store=True, default=False)
    #
    # check_in = fields.Datetime(required=False)
    date = fields.Date(store=True, compute="_compute_attendance_date")
    day = fields.Char(store=True, compute="_compute_day_total", required=False)

    @api.depends("check_in", "check_out")
    def _compute_attendance_date(self):
        for attendance in self:
            print(self.check_in.date(), "--")
            attendance.date = self.check_in.date()

    # shift = fields.Char(compute="_compute_shift")
    # time_remarks_in = fields.Char(
    #     store=True, string="Late In", compute='_compute_date_remarks_late_in')
    # time_remarks_out = fields.Char(
    #     store=True, string="Late Out", compute='_compute_late_out')
    remarks = fields.Char(store=True, compute="_compute_date_remarks_late_in")

    # @api.constrains('check_in', 'check_out', 'employee_id')
    # def _check_validity(self):
    #     """ Verifies the validity of the attendance record compared to the others from the same employee.
    #         For the same employee we must have :
    #             * maximum 1 "open" attendance record (without check_out)
    #             * no overlapping time slices with previous employee records
    #     """
    #     for attendance in self:
    #         # we take the latest attendance before our check_in time and check it doesn't overlap with ours
    #         last_attendance_before_check_in = self.env['hr.attendance'].search([
    #             ('employee_id', '=', attendance.employee_id.id),
    #             ('check_in', '<=', attendance.check_in),
    #             ('id', '!=', attendance.id),
    #         ], order='check_in desc', limit=1)
    #         if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
    #             raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
    #                 'empl_name': attendance.employee_id.name,
    #                 'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
    #             })
    #
    #         # we verify that the latest attendance with check_in time before our check_out time
    #         # is the same as the one before our check_in time computed before, otherwise it overlaps
    #         last_attendance_before_check_out = self.env['hr.attendance'].search([
    #             ('employee_id', '=', attendance.employee_id.id),
    #             ('check_in', '<', attendance.check_out),
    #             ('id', '!=', attendance.id),
    #         ], order='check_in desc', limit=1)
    #         if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
    #             raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
    #                 'empl_name': attendance.employee_id.name,
    #                 'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in, dt_format=False),
    #             })
    #
    # @api.constrains('check_in', 'check_out')
    # def _check_validity_check_in_check_out(self):
    #     """ verifies if check_in is earlier than check_out. """
    #     for attendance in self:
    #         if attendance.check_in and attendance.check_out:
    #             if attendance.check_out < attendance.check_in:
    #                 attendance.check_out = False
    #
    #
    # @api.constrains('check_in', 'check_out')
    # def _check_double_check_in(self):
    #     for attendance in self:
    #         self.search([('check_in', '=', attendance.check_in), ('id', '!=', attendance.id)]).unlink()
    #
    # @api.depends('check_in')
    # def _compute_late_in_hours(self):
    #
    #     for rec in self:
    #
    #         rec.late_in_hrs = 0.0
    #         user_tz = pytz.timezone('UTC')
    #         local_dt = pytz.utc.localize(dt=datetime.now()).astimezone(user_tz)
    #         week_day = local_dt.weekday()
    #         if rec.employee_id.resource_calendar_id:
    #             working_time_calendar = rec.sudo().employee_id.resource_calendar_id
    #             work_hours = working_time_calendar.attendance_ids
    #             for daily_work_hour in work_hours:
    #                 if daily_work_hour.dayofweek == str(week_day) and daily_work_hour.day_period == 'standard':
    #                     work_from = daily_work_hour.hour_from
    #                     work_from_in_time_form = '{0:02.0f}:{1:02.0f}'.format(
    #                         *divmod(work_from * 60, 60))  # float value of work from is converted to time
    #                     str_time = local_dt.strftime("%H:%M")
    #                     check_in_date = datetime.strptime(
    #                         str_time, "%H:%M").time()
    #                     hour_from_date = datetime.strptime(
    #                         work_from_in_time_form, "%H:%M").time()
    #                     t1 = timedelta(hours=check_in_date.hour,
    #                                    minutes=check_in_date.minute)
    #                     t2 = timedelta(hours=hour_from_date.hour,
    #                                    minutes=hour_from_date.minute)
    #
    #                     if check_in_date > hour_from_date:
    #
    #                         final = t1 - t2
    #
    #                         rec.late_in_hrs = final.total_seconds() / 3600
    #                     break
    #
    # @api.depends('check_out')
    # def _compute_early_out_hours(self):
    #
    #     for rec in self:
    #         if not rec.check_out:
    #             continue
    #
    #         rec.early_out_hrs = 0.0
    #         user_tz = pytz.timezone('UTC')
    #         local_dt = pytz.utc.localize(rec.check_out).astimezone(user_tz)
    #         week_day = local_dt.weekday()
    #         if rec.employee_id.resource_calendar_id:
    #             working_time_calendar = rec.sudo().employee_id.resource_calendar_id
    #             work_hours = working_time_calendar.attendance_ids
    #             for daily_work_hour in work_hours:
    #                 if daily_work_hour.dayofweek == str(week_day) and daily_work_hour.day_period == 'standard':
    #                     work_to = daily_work_hour.hour_to
    #                     work_to_in_time_form = '{0:02.0f}:{1:02.0f}'.format(
    #                         *divmod(work_to * 60, 60))  # float value of work to is converted to time
    #                     str_time = local_dt.strftime("%H:%M")
    #                     check_out_date = datetime.strptime(
    #                         str_time, "%H:%M").time()
    #                     hour_to_date = datetime.strptime(
    #                         work_to_in_time_form, "%H:%M").time()
    #                     t1 = timedelta(hours=check_out_date.hour,
    #                                    minutes=check_out_date.minute)
    #                     t2 = timedelta(hours=hour_to_date.hour,
    #                                    minutes=hour_to_date.minute)
    #
    #                     if check_out_date < hour_to_date:
    #
    #                         final = t2 - t1
    #
    #                         rec.early_out_hrs = final.total_seconds() / 3600
    #                     break
    #
    # @api.onchange('check_in', 'check_out')
    # def _restrict_check_in_check_out(self):
    #
    #     user_tz = pytz.timezone('UTC')
    #
    #     current_dt_user_tz = pytz.utc.localize(
    #         datetime.now()).astimezone(user_tz)
    #
    #     if pytz.utc.localize(self.check_in).astimezone(user_tz) > current_dt_user_tz:
    #
    #         raise UserError(
    #             _("The check in and check out can not be greater than current datetime"))
    #
    #     if self.check_out and pytz.utc.localize(self.check_out).astimezone(user_tz) > current_dt_user_tz:
    #         raise UserError(
    #             _("The check in and check out can not be greater than current datetime"))
    #
    @api.depends("check_in", "check_out")
    def _compute_date_remarks_late_in(self):
        """
        Computes date from the check in date, remarks based on whether the employee has chekced in, and determines
        how late the employee checked in from the standard time
        """
        for record in self:
            user_timezone = pytz.timezone("UTC")

            if record.check_in:
                record.remarks = "Present"

                timezone_check_in = pytz.utc.localize(record.check_in).astimezone(
                    user_timezone
                )
                check_in_time = datetime.strptime(
                    str(record.check_in), "%Y-%m-%d %H:%M:%S"
                )

                record.date = timezone_check_in.date()
                check_in_time = timezone_check_in.time()
                check_in_standard = time(10, 0, 0)

                if check_in_time > check_in_standard:
                    check_in_time = datetime.strptime(str(check_in_time), "%H:%M:%S")
                    check_in_standard = datetime.strptime(
                        str(check_in_standard), "%H:%M:%S"
                    )

            else:
                record.remarks = "Absent"

    #
    # @api.depends('check_out')
    # def _compute_late_out(self):
    #     """
    #     Computes whether the employee has left later than the standard time based on the standard check-out time
    #     """
    #     for record in self:
    #
    #         if record.check_out:
    #             user_timezone = pytz.timezone('UTC')
    #             timezone_check_out = pytz.utc.localize(
    #                 record.check_out).astimezone(user_timezone)
    #
    #             check_out_time = datetime.strptime(
    #                 str(record.check_out), '%Y-%m-%d %H:%M:%S')
    #             check_out_time = timezone_check_out.time()
    #
    #             check_out_standard = time(17, 0, 0)
    #             if check_out_time > check_out_standard:
    #                 check_out_time = datetime.strptime(
    #                     str(check_out_time), "%H:%M:%S")
    #                 check_out_standard = datetime.strptime(
    #                     str(check_out_standard), "%H:%M:%S")
    #                 difference = check_out_time - check_out_standard
    #                 record.time_remarks_out = f"Late Out by ({difference})"
    #             else:
    #                 record.time_remarks_out = False
    #         else:
    #             record.time_remarks_out = False
    #
    @api.depends("date")
    def _compute_day_total(self):
        """
        Computes day based on the date
        """
        for record in self:
            if record.date:
                record.ensure_one()

                day_name = datetime.strptime(
                    record.date.strftime("%d/%m/%Y"), "%d/%m/%Y"
                ).weekday()
                record.day = calendar.day_name[day_name]

    #
    # @api.depends('day')
    # def _compute_shift(self):
    #     """
    #     Fills in the standard shift times for each day, except Saturday and Sunday, when the shift is left blank
    #     """
    #     for record in self:
    #         if record.day != "Saturday" and record.day != "Sunday":
    #             record.shift = "09:00:00 - 17:00:00"
    #         else:
    #             record.shift = False
    #
    #
    # def create(self, vals):
    #     prev_attendance = self.search([('check_in','=',vals['check_in'])])
    #     if prev_attendance:
    #         raise UserError('Attendance already exists for this date')
    #     res = super(HrAttendance, self).create(vals)
    #     return res
