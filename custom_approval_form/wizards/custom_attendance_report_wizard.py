from odoo import models, fields, api
from datetime import datetime, time

class AttendanceWizard(models.TransientModel):
    _name = 'attendance.wizard'
    _description = 'Attendance Wizard'

    employee_ids = fields.Many2many('hr.employee', string="Employees")
    date_from = fields.Date(string="From Date", required=True)
    date_to = fields.Date(string="To Date", required=True)

    def attendance_of_employee(self):
        for wizard in self:
            dt_from = datetime.combine(wizard.date_from, time.min)
            dt_to = datetime.combine(wizard.date_to, time.max)
            employees = wizard.employee_ids or self.env['hr.employee'].search([])
            all_attendance_data = []

            for emp in employees:
                attendance_data = self.env['hr.attendance'].search([('employee_id', '=', emp.id),('check_in', '>=', dt_from),('check_out', '<=', dt_to),])

                for attendance_emp in attendance_data:
                    attendance_info = {
                        'employee_name': attendance_emp.employee_id.name,
                        'check_in': attendance_emp.check_in,
                        'check_out': attendance_emp.check_out,
                        'worked_hours': attendance_emp.worked_hours,
                        'extra_hours': attendance_emp.overtime_hours,
                    }
                    all_attendance_data.append(attendance_info)
                    
            
            return all_attendance_data

    def attendance_pdf_report(self):

        return self.env.ref('custom_approval_form.custom_attendance_employee_action').report_action(self)