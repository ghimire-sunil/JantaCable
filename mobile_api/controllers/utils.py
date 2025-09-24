import jwt
from pytz import timezone
from functools import wraps
from enum import Enum


from odoo.http import request

SECRET_KEY = "e4ed318a3d593bc39dd84049e8f0354a9a93a7330c2ff54c3dd8d1408d8f94c2a9625752df5069572893bb691c0b9aecf36c7bf7fbd807fb7f4f69bbbe72fec7900b57898529e442e0832b10303a4765781e712a7bc125af34118bada00d925aede2954eaaa15827c8a038349ee1ec06b11197b20732ba5a80d62e7f1c4d462a27930df6e35b34f4f9ae01b18d11daebd341c734588ce91c5760b62669c642c92ad17be5184f63f1eddbdb0a77b1eef60bddc94b4aa2953b6ae4e17bd108626a9fa9d172c03342f170e858466605f42f4e9c1269a123ac5627054644eb5f3f25e18ab25f7631e6aaf0eb7dfc2f8e12e6a708417029b9779a35adb15fb17c72ea735c8407f386337f5d66862997b0bd6f622bfd58d71f4feefd84090ea44ff7ceed006e931aa54f347e79015823a365a9717ff11e11d61994419f2d65618d677c72fe086e3eff971b04d48669f9efbf83d6afb82e5db76726ee9a4d12cf902aa6197020449847ffc74c43c16102e3ad4eec49fe9138c3d6851ade8e89931af9eaf6aadeb253040b6eeb5cde8b4652f424f258fdce0a5ee11b44c77416fb45e237c319a51ebed920689da0309f388b542b4e258123ced611d62da207207d26ce8a5e2f405e4759fe32e76104bc2bfd05d30e64a9fe391c8f2c0631b3a3623c83c76bac2af863b42ff2c9c78e0a8d482a5ac0ebb3d2f8909f2f47036fe3e164f231"
TIMEZONE = timezone("Asia/Kathmandu")
ALLOWED_URL = "*"


class UserRole(Enum):
    SALE_PERSON = "sale_person"
    SALE_AGENT = "sale_agent"
    CUSTOMER = "customer"
    DELIVERY_PERSON = "delivery"


def required_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            token = request.httprequest.headers.get("Authorization")
            if not token:
                raise Exception("Auth Token is missing")
            user_id = jwt.decode(
                jwt=token.split(" ")[1], key=SECRET_KEY, algorithms=["HS256"]
            )
            user = request.env["res.users"].sudo().browse(user_id["id"])
            if not user:
                raise Exception("User not Found")
            request.env.user = user
            return func(user=user, *args, **kwargs)

        except jwt.ExpiredSignatureError:
            return response(
                status=401,
                message="Your session has expired. Please log in again to continue .",
            )
        except Exception as e:
            print(e)
            return response(status=401, message=e.args[0])

    return wrapper


def response(status=200, message="Success", data=None):
    return {"status": status, "message": message, "data": data}


def formate_error(errors):
    error_response = []
    for error in errors:
        error_response.append(
            {
                "name": error.get("loc")[0],
                "error": error.get("msg"),
                "error_type": error.get("type"),
                "loc": error.get("loc"),
            }
        )

    return error_response


def check_role(allowed_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if request.env.user.role in allowed_roles:
                return func(*args, **kwargs)
            return response(
                status=401, message="You are not authorized to access this route"
            )
        return wrapper
    return decorator
