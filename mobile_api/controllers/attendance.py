from odoo import SUPERUSER_ID, http
from odoo.http import request, Response
from pydantic import ValidationError
from .schema.attendance import Attendance
from .utils import ALLOWED_URL, response, formate_error, required_login, check_role, UserRole
from datetime import date, datetime, timedelta, time
import calendar
import json
import base64

class AttendanceController(http.Controller):

    def make_response(func):
        def inner(*args,**kwargs):
            result = func(*args,**kwargs)
            headers = {"Access-Control-Allow-Origin": "*"}
            return Response(json.dumps({
                'result':result
            }),headers=headers, content_type='application/json', status=200)  

        return inner

    @http.route('/api/v1/check-in', type='http', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @make_response
    def check_in(self, **kwargs):
        try:
            attendance = Attendance(**kwargs)
            employee = attendance.user.employee_id
            
            if not employee:
                raise Exception("No employee found for the currently logged in user!")
            
            current_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.now().strftime('%Y-%m-%d 00:00:00'))
            ], limit=1)
            
            if current_attendance:
                if not current_attendance.check_out:
                    raise Exception("The employee already has an attendance record for this date!!")
                elif current_attendance.check_out >= datetime.now():
                    raise Exception("The employee already has an attendance record for this date!!")
            
            new_attendance = employee.with_user(SUPERUSER_ID)._attendance_action_change({
                'latitude': float(attendance.latitude),
                'longitude': float(attendance.longitude),
                'mode': 'systray',
            })
            
            image_base64 = False
            if attendance.image:
                image = attendance.image
                image_base64 = base64.b64encode(image.read())

            new_attendance.image_1920 = image_base64

            return {
                'result': {
                    "status": 200,
                    "message": 'Checked in successfully!!',
                    "data": None
                }
            }
                 
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        
    @http.route('/api/v1/check-out', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def check_out(self, **kwargs):
        try:
            employee = request.env.user.employee_id
            if not employee:
                raise Exception("No employee found for the currently logged in user!")
            
            current_attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', datetime.now().strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<=', datetime.now().strftime('%Y-%m-%d 23:59:59'))
            ], limit=1)

            if not current_attendance:
                raise Exception("No check-in record found for this date!!")
            elif current_attendance.check_out:
                raise Exception("Already checked out for this date!!")
            
            employee.with_user(SUPERUSER_ID)._attendance_action_change({
                'latitude': float(kwargs.get('latitude')),
                'longitude': float(kwargs.get('longitude')),
                'mode': 'systray',
            })
            
            return response(
                status=200,
                message="Checked out successfully!",
                data=None
            )
  
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        
    @http.route('/api/v1/attendance-status', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def attendance_status(self, **kwargs):
        try:
            employee = request.env.user.employee_id

            if not employee:
                raise Exception("No employee found for the currently logged in user!")
            
            current_date = date.today()
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', current_date.strftime('%Y-%m-%d 00:00:00')),
                ('check_in', '<=', current_date.strftime('%Y-%m-%d 23:59:59'))
            ], limit=1)

            data = []

            if attendance:

                check_in = attendance.check_in + timedelta(hours=5,minutes=45)
                check_out = False
                worked_time = False

                if attendance.check_out:
                    check_out = attendance.check_out + timedelta(hours=5,minutes=45)

                if attendance.worked_hours:
                    hours, minutes = divmod(abs(attendance.worked_hours) * 60, 60)
                    minutes = round(minutes)
                    if minutes == 60:
                        minutes = 0
                        hours += 1
                    if attendance.worked_hours < 0:
                        worked_time = '-%02d:%02d' % (hours, minutes)
                    worked_time = '%02d:%02d' % (hours, minutes)

                data.append({
                    'check_in': check_in,
                    'check_out': check_out,
                    'worked_hours': worked_time
                })
                message = "Attendance fetched successfully!"
            else:
                message = "No attendance found for today!!"
            
            return response(
                status=200,
                message=message,
                data=data
            )
  
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        
    @http.route('/api/v1/active-status', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def active_status(self, **kwargs):
        try:
            employee = request.env.user.employee_id
            activity = "Not Active"

            if not employee:
                raise Exception("No employee found for the currently logged in user!")
            
            current_date = date.today()
            attendance = request.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', current_date.strftime('%Y-%m-%d 00:00:00'))
            ], limit=1)
            
            if attendance:
                if not attendance.check_out:
                    activity = "Active"
                elif attendance.check_out >= datetime.now():
                    activity = "Active"

            
            return response(
                status=200,
                message="Activity Fetched Successfully!",
                data={
                    'activity': activity
                }
            )
  
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )


    @http.route('/api/v1/attendance-history', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    def attendance_history(self, **kwargs):
        try:
            employee = request.env.user.employee_id

            if not employee:
                raise Exception("No employee found for the currently logged in user!")
            
            current_year = date.today().year
            current_month = date.today().month

            time_start = time(00, 00, 00)
            time_end = time(23, 59, 59)

            data = []

            for month in range(1,current_month+1):
                worked_hours = 0
                _, num_days = calendar.monthrange(current_year, month)
                month_start = date(current_year, month, 1)
                month_end = date(current_year, month, num_days)

                start = datetime.combine(month_start, time_start)
                end = datetime.combine(month_end, time_end)

                month_data = {
                    'month': calendar.month_name[month],
                    'total_worked_hours': worked_hours,
                    'attendances': []
                }

                attendances = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', start),
                    ('check_out','<=', end)
                ], order="check_in asc")
                
                for attendance in attendances:
                    check_in = attendance.check_in + timedelta(hours=5,minutes=45)
                    check_out = False
                    worked_time = False

                    if attendance.check_out:
                        check_out = attendance.check_out + timedelta(hours=5,minutes=45)

                    if attendance.worked_hours:
                        hours, minutes = divmod(abs(attendance.worked_hours) * 60, 60)
                        minutes = round(minutes)
                        if minutes == 60:
                            minutes = 0
                            hours += 1
                        if attendance.worked_hours < 0:
                            worked_time = '-%02d:%02d' % (hours, minutes)
                        worked_time = '%02d:%02d' % (hours, minutes)

                    month_data['attendances'].append({
                        'check_in': check_in,
                        'check_out': check_out,
                        'worked_hours': worked_time
                    })

                    worked_hours += attendance.worked_hours

                if worked_hours > 0:
                    hours, minutes = divmod(abs(worked_hours) * 60, 60)
                    minutes = round(minutes)
                    if minutes == 60:
                        minutes = 0
                        hours += 1
                    if worked_hours < 0:
                        worked_hours = '-%02d:%02d' % (hours, minutes)
                    worked_hours = '%02d:%02d' % (hours, minutes)

                month_data['total_worked_hours'] = worked_hours
                
                data.append(month_data)

            return response(
                status=200,
                message="Attendance History Fetched Successfully!",
                data=data
            )
  
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )
        

    @http.route('/api/v1/team-members-activity', type='json', auth='public', csrf=False, cors=ALLOWED_URL)
    @required_login
    @check_role([UserRole.SALE_AGENT.value])
    def active_team_members(self, **kwargs):
        try:
            team = request.env['crm.team'].sudo().search([('user_id','=',request.env.user.id)])
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            data = []

            for member in team.member_ids:
                employee = member.employee_id

                if not employee:
                    raise Exception(f"No employee found for {member.name}")
                
                activity = "Not Active"
                check_in = False
                check_out = False

                current_date = date.today()
                attendance = request.env['hr.attendance'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('check_in', '>=', current_date.strftime('%Y-%m-%d 00:00:00'))
                ], limit=1)
                
                if attendance:
                    check_in = attendance.check_in + timedelta(hours=5,minutes=45)
                    if attendance.check_out:
                        check_out = attendance.check_out + timedelta(hours=5,minutes=45)
                    if not attendance.check_out:
                        activity = "Active"
                    elif attendance.check_out >= datetime.now():
                        activity = "Active"

                today_orders = request.env['distributor.order'].sudo().search_count([('user_id', '=',member.id), ('order_date','=',date.today())])
                today_visited = request.env['res.partner'].sudo().search_count([('is_visited_today','=',True), ('visited_by','=', member.id)])

                data.append({
                    "id": member.id,
                    "name": member.name,
                    "image": f"{system_url}/web/image/res.users/{member.id}/avatar_128",
                    "check_in": check_in,
                    "check_out": check_out,
                    "active_status": activity,
                    "today_orders": today_orders,
                    "today_visted_stores": today_visited
                })

            return response(
                status=200,
                message="Members and their active status fetched successfully!",
                data=data
            )
  
        except ValidationError as error:    
            return response(
                status=400,
                message="Data Validation Error",
                data=formate_error(error.errors())
            )
        
        except Exception as e:
            return response(
                status=400,
                message=e.args[0],
                data=None
            )