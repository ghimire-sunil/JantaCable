from odoo import fields, models, api, _

class ApprovalRequest(models.Model):
    _inherit = "approval.request"

    behalf_worker_id = fields.Many2one('hr.employee',string="Working On Behalf")


    def count_employee_leaves(self):
        for rec in self:
            employee_id_find = rec.request_owner_id.employee_id
            
            leave_of_employee = self.env['hr.leave'].search([('employee_id','=',employee_id_find.id)])

            leave_data = []
            grand_total = 0
            for leave in leave_of_employee:
                leave_data.append({
                    'leave_name': leave.holiday_status_id.name,
                    'leave_from': leave.date_from,
                    'leave_to': leave.date_to,
                    'total_day': leave.duration_display,
                    'leave_remark': leave.name,
                })
                grand_total += leave.number_of_days

            return {
                'leaves': leave_data,
                'grand_total': grand_total,
            }

    # def amount_word(self):