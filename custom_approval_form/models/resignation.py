
from odoo import Command, fields, models
import base64


class HrDepartureWizard(models.TransientModel):
    _inherit = 'hr.departure.wizard'


    def mail_sending_stage_lead(self,activity_type):
        # mail sending with attachment for approval of resignation
        # approval
        if activity_type == 'resignation_approval':
            # approval letter
            report_template_id = self.env['ir.actions.report'].with_context(force_report_rendering=True)._render_qweb_pdf('custom_approval_form.custom_resignation_action', res_ids=self.id)
            template = self.env.ref('custom_approval_form.resignation_email_template_name')

        elif activity_type == 'resignation_handover':
            # handover
            report_template_id = self.env['ir.actions.report'].with_context(force_report_rendering=True)._render_qweb_pdf('custom_approval_form.custom_resignation_handover_action', res_ids=self.id)
            template = self.env.ref('custom_approval_form.resignation_email_template_name')
            
        elif activity_type == 'final_interview':
            # final interview
            report_template_id = self.env['ir.actions.report'].with_context(force_report_rendering=True)._render_qweb_pdf('custom_approval_form.custom_resignation_final_interview_action', res_ids=self.id)
            template = self.env.ref('custom_approval_form.resignation_email_template_name')
            

        data_record = base64.b64encode(report_template_id[0])
        ir_values = {
            'name': "Resignation Form",
            'type': 'binary',
            'datas': data_record,
            'store_fname': data_record,
            'mimetype': 'application/x-pdf',
        }
        data_id = self.env['ir.attachment'].create(ir_values)
        # template = self.env.ref('custom_approval_form.resignation_email_template_name')
        template.attachment_ids = [(6, 0, [data_id.id])]

        template.send_mail(self.id, force_send=True)
        template.attachment_ids = [(3, data_id.id)]

        # create a crm stage and lead
        if activity_type == 'resignation_approval':
            stage = self.env['crm.stage'].search([('name', '=', 'Resignation Approval')], limit=1)
            if not stage:
                stage = self.env['crm.stage'].create({
                    'name': 'Resignation Approval',
                    'sequence': 5,
                })

            self.env['crm.lead'].create({
                'name': f'Resignation of {self.employee_id.name}',
                'stage_id': stage.id,
                'description': f'Employee {self.employee_id.name} has resigned.',
                'type': 'opportunity',
            })
        


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def action_feedback_schedule_next(self, feedback=False, attachment_ids=None):
        employee_activities = self.filtered(lambda act: act.res_model == "hr.employee")
        other_activities = self - employee_activities
        for activity in employee_activities:
            activity_data = self.env['mail.activity.plan.template'].search([('summary','=',activity.summary)])
            
            employee = self.env[activity.res_model].browse(activity.res_id)
            wizard = self.env['hr.departure.wizard'].create({'employee_id': employee.id,})
            if activity_data.select_activity_type == 'resignation_approval':
                wizard.mail_sending_stage_lead(activity_data.select_activity_type)
                super().action_feedback_schedule_next( feedback=False, attachment_ids=None)
                
            elif activity_data.select_activity_type == 'resignation_handover':
                wizard.mail_sending_stage_lead(activity_data.select_activity_type)
                super().action_feedback_schedule_next( feedback=False, attachment_ids=None)
                
            elif activity_data.select_activity_type == 'final_interview':
                wizard.mail_sending_stage_lead(activity_data.select_activity_type)
                super().action_feedback_schedule_next( feedback=False, attachment_ids=None)
        # if not employee module call this super function
        if other_activities:
            super().action_feedback_schedule_next( feedback=False, attachment_ids=None)

    def action_feedback(self, feedback=False, attachment_ids=None):
        employee_activities = self.filtered(lambda act: act.res_model == "hr.employee")
        other_activities = self - employee_activities
        for activity in employee_activities:
            activity_data = self.env['mail.activity.plan.template'].search([('summary','=',activity.summary)])
            
            employee = self.env[activity.res_model].browse(activity.res_id)
            wizard = self.env['hr.departure.wizard'].create({'employee_id': employee.id,})
            if activity_data.select_activity_type == 'resignation_approval':
                wizard.mail_sending_stage_lead(activity_data.select_activity_type)
                super().action_feedback(feedback=False, attachment_ids=None)
                
            elif activity_data.select_activity_type == 'resignation_handover':
                wizard.mail_sending_stage_lead(activity_data.select_activity_type)
                super().action_feedback(feedback=False, attachment_ids=None)
                
            elif activity_data.select_activity_type == 'final_interview':
                wizard.mail_sending_stage_lead(activity_data.select_activity_type)
                super().action_feedback(feedback=False, attachment_ids=None)
                
        if other_activities:
            super().action_feedback(feedback=False, attachment_ids=None)

class MailActivityPlanTemplate(models.Model):
    _inherit = "mail.activity.plan.template"

    select_activity_type = fields.Selection([('resignation_approval', 'Resignation Approval'),('resignation_handover', 'Resignation Handover'),('final_interview', 'Final Interview'),],string="Email Type")
        

        
    
