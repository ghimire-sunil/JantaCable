from odoo import SUPERUSER_ID, http
from odoo.http import request, Response
from pydantic import ValidationError
from .utils import response, required_login, formate_error, check_role, UserRole
from datetime import date, datetime, timedelta
import ast
import json
import base64

class GamificationController(http.Controller):

    @http.route("/api/v1/leaderboard-ranking", type="json", csrf=False, auth="public")
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def leaderboard_ranking(self, **kw):
        try:
            user = request.env.user
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            if user.role == 'sale_person':
                challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', [user.id]), ("state", "=", "inprogress")])
                team_members = request.env['crm.team.member'].sudo().search([('user_id','=',user.id)])
                team = request.env['crm.team'].sudo().search([('crm_team_member_ids','in',team_members.ids)], limit=1)
            else:
                team = request.env['crm.team'].sudo().search([('user_id','=',user.id)], limit=1)
                challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', team.member_ids.ids), ("state", "=", "inprogress")])

            challenge_details = []

            for challenge in challenges:
                goal_details = []
                if challenge.visibility_mode == 'ranking':
                    lines_boards = challenge._get_serialized_challenge_lines(restrict_goals=False)
                    for line in lines_boards:
                        rank = 0
                        ranks = []
                        for goal in line['goals']:
                            if goal['user_id'] in team.member_ids.ids:
                                rank += 1
                                ranks.append({
                                    "user_id": goal['user_id'],
                                    "name": goal['name'],
                                    "image": f"{system_url}/web/image/res.users/{goal['user_id']}/avatar_128", 
                                    "rank": rank,
                                    "current": goal['current'],
                                    "achieved_percent": goal['completeness'],
                                    "state": goal['state']
                                })
                        goal_details.append({
                            'name': line['name'],
                            'target': line['target'],
                            'ranks': ranks
                        })
                    challenge_details.append({
                        'name': challenge.name,
                        'participants': challenge.user_count,
                        'goals': goal_details
                    })

            data = ({
                "challenges": challenge_details
            })

            return response(
                    status=200,
                    message="Leaderboard successfully fetched!!",
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


    @http.route("/api/v1/challenges", type="json", csrf=False, auth="public")
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def get_challenges(self, **kw):
        try:
            user = request.env.user
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            if user.role == 'sale_person':
                challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', [user.id]), ("state", "=", "inprogress")])
                team_members = request.env['crm.team.member'].sudo().search([('user_id','=',user.id)])
                team = request.env['crm.team'].sudo().search([('crm_team_member_ids','in',team_members.ids)], limit=1)
            else:
                team = request.env['crm.team'].sudo().search([('user_id','=',user.id)], limit=1)
                challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', team.member_ids.ids), ("state", "=", "inprogress")])

            challenge_details = []

            for challenge in challenges:
                if challenge.visibility_mode == 'ranking':
                    challenge_details.append({
                        'id': challenge.id,
                        'name': challenge.name,
                        'participants': challenge.user_count,
                        'goals': len(challenge.line_ids)
                    })

            data = ({
                "challenges": challenge_details
            })

            return response(
                    status=200,
                    message="Challenges successfully fetched!!",
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
        
    
    @http.route("/api/v1/goals", type="json", csrf=False, auth="public")
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def get_goals(self, **kw):
        try:
            user = request.env.user
            challenge_id = kw['challenge_id']

            # if user.role == 'sale_person':
            #     challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', [user.id]), ("state", "=", "inprogress")])
            #     team_members = request.env['crm.team.member'].sudo().search([('user_id','=',user.id)])
            #     team = request.env['crm.team'].sudo().search([('crm_team_member_ids','in',team_members.ids)], limit=1)
            # else:
            #     team = request.env['crm.team'].sudo().search([('user_id','=',user.id)], limit=1)
            #     challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', team.member_ids.ids), ("state", "=", "inprogress")])

            if not challenge_id:
                raise Exception("Challenge ID required!!")
            
            challenge = request.env['gamification.challenge'].sudo().search([('id','=',challenge_id), ("state", "=", "inprogress")])

            goal_details = []
            if challenge.visibility_mode == 'ranking':
                lines_boards = challenge._get_serialized_challenge_lines(restrict_goals=False)
                for line in lines_boards:
                    for goal in line['goals']:
                        goal_id = request.env['gamification.goal'].sudo().search([('id','=',goal['id'])])
                        id_ = goal_id.definition_id
                    goal_details.append({
                        'id': id_.id,
                        'name': line['name'],
                        'target': line['target'],
                    })

            data = ({
                "goals": goal_details
            })

            return response(
                    status=200,
                    message="Goals successfully fetched!!",
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
        
        
    @http.route("/api/v1/ranks", type="json", csrf=False, auth="public")
    @required_login
    @check_role([UserRole.SALE_PERSON.value, UserRole.SALE_AGENT.value])
    def get_ranks(self, **kw):
        try:
            user = request.env.user
            challenge_id = kw['challenge_id']
            goal_id = kw['goal_id']
            system_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')

            if not challenge_id or not goal_id:
                raise Exception("Both challenge ID and goal ID required!!")
            
            challenge = request.env['gamification.challenge'].sudo().search([('id','=',challenge_id), ("state", "=", "inprogress")])
            # goal_challenge = request.env['gamification.goal.definition'].sudo().browse(goal_id)

            if user.role == 'sale_person':
                # challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', [user.id]), ("state", "=", "inprogress")])
                team_members = request.env['crm.team.member'].sudo().search([('user_id','=',user.id)])
                team = request.env['crm.team'].sudo().search([('crm_team_member_ids','in',team_members.ids)], limit=1)
            else:
                team = request.env['crm.team'].sudo().search([('user_id','=',user.id)], limit=1)
                # challenges = request.env['gamification.challenge'].sudo().search([('user_ids.id', 'in', team.member_ids.ids), ("state", "=", "inprogress")])

            ranks = []

            if challenge.visibility_mode == 'ranking':
                goal_line_id = request.env['gamification.goal'].sudo().search([('definition_id','=',goal_id), ('challenge_id','=',challenge_id)])
                if goal_line_id:
                    lines_boards = challenge._get_serialized_challenge_lines(restrict_goals=goal_line_id)
                    for line in lines_boards:
                        rank = 0
                        for goal in line['goals']:
                            if goal['user_id'] in team.member_ids.ids:
                                rank += 1
                                ranks.append({
                                    "user_id": goal['user_id'],
                                    "name": goal['name'],
                                    "image": f"{system_url}/web/image/res.users/{goal['user_id']}/avatar_128", 
                                    "rank": rank,
                                    "current": goal['current'],
                                    "achieved_percent": goal['completeness'],
                                    "state": goal['state']
                                })

            data = ({
                "ranks": ranks
            })

            return response(
                    status=200,
                    message="Ranks successfully fetched!!",
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
