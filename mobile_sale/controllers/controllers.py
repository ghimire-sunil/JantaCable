# -*- coding: utf-8 -*-
import os
from odoo import http, Command, SUPERUSER_ID
from odoo.http import request, Response
from functools import wraps
import json
from odoo.addons.payment.controllers.portal import PaymentPortal
import jwt
import logging
from . import constant
from datetime import datetime
import base64

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

import psycopg2

_logger = logging.getLogger(__name__)

import math, random


# function to generate OTP
def generateOTP():
    # Declare a digits variable
    # which stores all digits
    digits = "0123456789"
    OTP = ""

    # length of password can be changed
    # by changing value in range
    for i in range(4):
        OTP += digits[math.floor(random.random() * 10)]

    return OTP


def endoceJwt(token, secret_key):
    user = None
    try:
        user = jwt.decode(token, secret_key, algorithms="HS256")
    except Exception as e:
        print(e)
    return user


def decode_bytes(result):
    if isinstance(result, (list, tuple)):
        decoded_result = []
        for item in result:
            decoded_result.append(decode_bytes(item))
        return decoded_result
    if isinstance(result, dict):
        decoded_result = {}
        for k, v in result.items():
            decoded_result[decode_bytes(k)] = decode_bytes(v)
        return decoded_result
    if isinstance(result, bytes):
        return result.decode("utf-8")
    return result


class make_response:
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            headers = {"Access-Control-Allow-Origin": "*"}
            try:
                result = decode_bytes(func(*args, **kwargs))
                if result:
                    return Response(
                        json.dumps(result),
                        headers=headers,
                        content_type="application/json",
                        status=200,
                    )
                else:
                    return Response(
                        json.dumps(result),
                        headers=headers,
                        content_type="application/json",
                        status=404,
                    )
            except Exception as e:
                return json.dumps({"error": str(e)})

        return wrapper


class MobileSale(http.Controller):
    @http.route(
        "/mobile/api/login", type="json", auth="public", csrf=False, method=["POST"]
    )
    def login(self, **kw):
        email = kw.get("email")
        password = kw.get("password")

        if email is None or password is None:
            return {"status": 400, "message": "Missing fields"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )

        try:
            userId = request.session.authenticate(
                request.env.cr.dbname,
                {
                    "login": kw.get("email"),
                    "password": kw.get("password"),
                    "type": "password",
                },
            )

        except:
            return {"status": 400, "message": "Email or Password Incorrect !!"}

        if not userId:
            return {"status": 403, "message": "access denied"}

        user = request.env["res.users"].sudo().browse(userId["uid"])
        user = user.read(
            [
                "login",
                "name",
                "phone",
                "street",
                "partner_latitude",
                "partner_longitude",
            ]
        )[0]
        token = jwt.encode(user, secret_key, algorithm="HS256")
        return {"status": 201, "result": {"user": user, "token": token}}

    @http.route(
        "/mobile/api/register", methods=["POST"], csrf=False, type="json", auth="public"
    )
    def register(self, **kw):
        name = kw.get("name")
        email = kw.get("email")
        password = kw.get("password")
        phone = kw.get("phone")
        address = kw.get("address")

        if (
            phone is None
            or name is None
            or email is None
            or password is None
            or address is None
        ):
            return {"status": 400, "message": "Missing fields !!"}

        # check is email already exists
        user = request.env["res.users"].sudo().search([("login", "=", email)], limit=1)
        if user:
            return {"status": 400, "message": "Email already exists!!"}

        # create res_partner
        partner = (
            request.env["res.partner"]
            .with_user(SUPERUSER_ID)
            .create(
                {
                    "email": email,
                    "name": name,
                    "phone": phone,
                    "street": address,
                    "partner_latitude": kw.get("lat") or 0,
                    "partner_longitude": kw.get("long") or 0,
                }
            )
        )

        # create corresponding res users
        # search portal group
        group = (
            request.env["res.groups"]
            .with_user(SUPERUSER_ID)
            .search([("name", "=", "Portal")], limit=1)
        )

        userParam = {
            "name": name,
            "login": email,
            "password": password,
            "partner_id": partner.id,
            "company_id": 1,
            "groups_id": [(4, group.id)],
            "company_ids": [(4, 1)],
        }

        user = request.env["res.users"].with_user(SUPERUSER_ID).create(userParam)
        user = user.read(
            [
                "login",
                "name",
                "phone",
                "street",
                "partner_latitude",
                "partner_longitude",
                "image_128",
            ]
        )[0]

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )

        token = jwt.encode(user, secret_key, algorithm="HS256")

        return {"status": 201, "result": {"user": user, "token": token}}

    @http.route(
        "/mobile/api/register/public-key",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def register_public_key(self, **kw):
        public_key = kw.get("public_key")
        # print(email)
        if public_key is None:
            return {"status": 400, "message": "Missing public key"}

        token = request.httprequest.headers.get("Authorization")

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )

        if not token:
            return {"status": 403, "message": "Token Missing"}

        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        user = request.env["res.users"].sudo().browse(user["id"])

        try:
            user.write({"mobile_public_key": public_key})
        except Exception as e:
            return {
                "status": 500,
                "message": e.args[0],
                "result": None,
            }

        return {
            "status": 201,
            "message": "Public key registered successfully !!",
            "result": None,
        }

    @http.route(
        "/mobile/api/verify_signature",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def verify_signature(self, **kw):
        signature = kw.get("signature")
        uid = kw.get("uid")
        challenge = kw.get("challenge")

        print(signature)
        print(challenge)
        # print(email)
        if signature is None:
            return {"status": 400, "message": "Missing signature"}

        if uid is None:
            return {"status": 400, "message": "Missing uid"}

        try:
            user = request.env["res.users"].sudo().browse(uid)

            public_key_pem_format = f"""-----BEGIN PUBLIC KEY-----\n{user.mobile_public_key.strip()}\n-----END PUBLIC KEY-----"""

            public_key = serialization.load_pem_public_key(
                public_key_pem_format.encode()
            )

            public_key.verify(
                base64.b64decode(signature),
                challenge.encode(),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
            user = user.read(
                [
                    "login",
                    "name",
                    "phone",
                    "street",
                    "partner_latitude",
                    "partner_longitude",
                ]
            )[0]

            secret_key = (
                request.env["ir.config_parameter"]
                .sudo()
                .get_param("mobile_sale.secret_key", constant.secret_key)
            )

            token = jwt.encode(user, secret_key, algorithm="HS256")

            return {"status": 201, "result": {"user": user, "token": token}}

        except Exception as e:
            print(e)
            return {"status": 400, "message": e.args[0]}

    @http.route(
        "/mobile/api/request_challenge",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def request_challenge(self, **kw):
        uid = kw.get("uid")
        # print(email)

        if uid is None:
            return {"status": 400, "message": "Missing uid"}

        challenge = base64.b64encode(os.urandom(32)).decode("utf-8")
        try:
            user = request.env["res.users"].sudo().browse(uid)

            if not user:
                return {"status": 401, "message": "unauthenticated"}

            return {"status": 200, "result": {"challenge": challenge}}

        except Exception as e:
            return {"status": 401, "message": e.args[0]}

    @http.route(
        "/mobile/api/resetpassword",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def resetpassword(self, **kw):
        email = kw.get("email")
        # print(email)
        if email is None:
            return {"status": 400, "message": "Missing email"}
        try:
            request.env["res.users"].sudo().reset_password(email)
        except Exception as e:
            return {
                "status": 500,
                "message": "Email may not found!! Try again",
                "result": None,
            }

        return {
            "status": 201,
            "message": "Password reset sent instructions to the email",
            "result": None,
        }

    @http.route(
        "/mobile/api/changepassword",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def changepassword(self, **kw):
        old_password = kw.get("oldPassword")
        new_password = kw.get("newPassword")
        # print(email)
        token = request.httprequest.headers.get("Authorization")

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )

        if not token:
            return {"status": 403, "message": "Token Missing"}

        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}
        try:
            userId = request.session.authenticate(
                request.env.cr.dbname,
                {"login": user["login"], "password": old_password, "type": "password"},
            )
        except:
            return {"status": 403, "message": "Old Password Incorrect !!"}

        try:
            user = request.env["res.users"].sudo().browse(userId["uid"])
            user.password = new_password
            user._set_new_password()
        except Exception as e:
            return {
                "status": 500,
                "message": "Something went wrong in server",
                "result": None,
            }

        return {"status": 201, "message": "New Password is set", "result": None}

    @http.route(
        "/mobile/api/checkotp", type="json", methods=["POST"], csrf=False, auth="public"
    )
    def checkotp(self, **kw):
        otp = kw.get("otp")
        login = kw.get("email")
        # print(email)

        db_name = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.db_name", constant.db_name)
        )
        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )

        user = request.env["res.users"].sudo().search([("login", "=", login)])

        if not user:
            return {"status": 404, "message": "Email Not Found !!"}

        if otp != user.last_otp:
            return {"status": 403, "message": "Incorrect OTP !!"}

        return {
            "status": 201,
            "message": "OTP verified",
            "result": {"otp": otp, "id": user.id},
        }

    @http.route(
        "/mobile/api/changepasswordbyotp",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def checkpasswordbyotp(self, **kw):
        otp = kw.get("otp")
        id = kw.get("id")
        new_password = kw.get("password")

        db_name = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.db_name", constant.db_name)
        )
        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )

        user = request.env["res.users"].sudo().browse(id)

        if not user:
            return {"status": 404, "message": "Id Not Found !!"}
        if otp != user.last_otp:
            return {"status": 403, "message": "Incorrect OTP !!"}

        user.password = new_password
        user._set_new_password()
        user.write({"last_otp": None})

        return {
            "status": 201,
            "message": "Password Changed Successfully !!!",
            "result": None,
        }

    @http.route(
        "/mobile/api/generate", type="json", methods=["POST"], csrf=False, auth="public"
    )
    def generateotp(self, **kw):
        login = kw.get("email")

        user = request.env["res.users"].sudo().search([("login", "=", login)], limit=1)

        if not user:
            return {"status": 404, "message": "Email Not Found !!"}

        otp = generateOTP()
        user.write({"last_otp": otp})
        user._sent_password_otp()

        return {"status": 201, "message": "Success Fully Generated OTP", "result": None}

    @http.route(
        "/mobile/api/user", type="json", methods=["POST"], csrf=False, auth="public"
    )
    def getUser(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "result": None, "message": "Token Missing"}
        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)
        if not user:
            return {"status": 401, "result": None, "message": "Token Expired !!"}
        user = request.env["res.users"].sudo().browse(user["id"])

        user_data = user.read(
            [
                "name",
                "login",
                "phone",
                "street",
                "image_128",
                "partner_latitude",
                "partner_longitude",
            ]
        )[0]

        return {"status": 200, "result": {"user": user_data}}

    @http.route(
        "/mobile/api/user/update",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def updateprofile(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "message": "Token Missing"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        name = kw.get("name")
        email = kw.get("email")
        phone = kw.get("phone")
        address = kw.get("address")

        if phone is None or name is None or email is None or address is None:
            return {"status": 400, "message": "Missing fields !!"}

        if user["login"] != email:
            is_exist = (
                request.env["res.users"].sudo().search([("login", "=", email)], limit=1)
            )
            if is_exist:
                return {"status": 400, "message": "Email used by another user!!"}

        # print(email)
        try:
            user = request.env["res.users"].with_user(SUPERUSER_ID).browse(user["id"])
            user.write(
                {
                    "login": email,
                    "phone": phone,
                    "street": address,
                    "name": name,
                    "email": email,
                    "partner_latitude": kw.get("lat") or 0,
                    "partner_longitude": kw.get("long") or 0,
                }
            )
        except Exception as e:
            return {"status": 500, "result": None, "message": "Something went wrong !!"}

        return {"status": 201, "result": None, "message": "Updated value!!"}

    @http.route(
        "/mobile/api/user/delete",
        type="json",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    def deleteUser(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "result": None, "message": "Token Missing"}
        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)
        if not user:
            return {"status": 401, "result": None, "message": "Token Expired !!"}
        user = request.env["res.users"].sudo().browse(user["id"])

        sale_orders = (
            request.env["sale.order"]
            .sudo()
            .search([("partner_id", "=", user.partner_id.id)])
        )

        if sale_orders.filtered(lambda x: x.mobile_delivery_status == "inprogress"):
            return {
                "status": 400,
                "message": "Your account has pending orders. Please Wait till order complete.",
            }

        user.sudo().mobile_public_key = False

        user.with_user(user.id).sudo()._deactivate_portal_user()

        return {"status": 200, "message": "Account Deleted !!"}

    @http.route(
        "/mobile/api/user/image",
        type="http",
        methods=["POST"],
        csrf=False,
        auth="public",
    )
    @make_response()
    def updateImage(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"result": {"status": 401, "message": "Token Missing"}}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"result": {"status": 401, "message": "Token Expired !!"}}

        image = kw.get("image")

        if image is None:
            return {"status": 400, "message": "Missing fields !!"}

        image_base64 = base64.b64encode(image.read())

        # print(email)
        try:
            user = request.env["res.users"].with_user(SUPERUSER_ID).browse(user["id"])
            user.write({"image_1920": image_base64})
        except Exception as e:
            return {
                "result": {
                    "status": 500,
                    "result": None,
                    "message": "Something went wrong !!",
                }
            }

        return {
            "result": {
                "status": 201,
                "result": None,
                "message": "Profile Picture Changed!!",
            }
        }

    @http.route("/mobile/api/products", auth="public")
    @make_response()
    def getProduct(self, **kw):
        products = (
            http.request.env["product.product"]
            .sudo()
            .search_read(
                [("website_published", "=", True)],
                [
                    "name",
                    "list_price",
                    "description_sale",
                    "mobile_minimum_order_quantity",
                ],
            )
        )
        # imageUrl =
        return products

    @http.route("/mobile/api/product/<int:id>", auth="public")
    @make_response()
    def productDetail(self, id, **kw):
        product = http.request.env["product.product"].sudo().browse(id)
        product = product.read(
            [
                "name",
                "image_512",
                "list_price",
                "description_sale",
                "mobile_minimum_order_quantity",
            ]
        )
        return product or {}

    @http.route("/mobile/api/sliders", auth="public", methods=["GET"])
    @make_response()
    def fetchSliders(self):
        result = (
            request.env["mobile.slider"].sudo().search(domain=[("active", "=", True)])
        )
        images = [
            f"web/image?model=mobile.slider&id={x.id}&field=image" for x in result
        ]

        return images

    @http.route(
        "/mobile/api/createOrder",
        methods=["POST"],
        type="json",
        csrf=False,
        auth="public",
    )
    def createOrder(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 403, "message": "Please Login to Create Order"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        partner_id = request.env["res.users"].sudo().browse(user["id"]).partner_id.id
        # partner_id=1
        order_id = kw.get("last_order_id")
        order = None
        if order_id:
            try:
                exisitng_order = request.env["sale.order"].sudo().browse(order_id)
                if (
                    exisitng_order.state == "draft"
                    and exisitng_order.partner_id.id == partner_id
                ):
                    order = exisitng_order
            except Exception as e:
                print(e)

        if order:
            # delete old order line
            for order_line in order.order_line:
                order_line.unlink()
            order.write(
                {
                    "order_line": [
                        (
                            0,
                            0,
                            {"product_id": x["id"], "product_uom_qty": x["quantity"]},
                        )
                        for x in kw.get("items")
                    ]
                }
            )
        else:
            # create completely new order
            order = (
                request.env["sale.order"]
                .with_user(SUPERUSER_ID)
                .create(
                    {
                        "partner_id": partner_id,
                        "team_id": request.env.ref(
                            "mobile_sale.salesteam_mobile_sales"
                        ).id,
                        "device_type": kw.get("device_type") or "android",
                        "order_line": [
                            (
                                0,
                                0,
                                {
                                    "product_id": x["id"],
                                    "product_uom_qty": x["quantity"],
                                },
                            )
                            for x in kw.get("items")
                        ],
                    }
                )
            )

        order._recompute_prices()

        result = order.read(["amount_total", "amount_tax", "amount_untaxed"])
        order_lines = order.order_line.read(
            ["product_id", "product_uom_qty", "price_unit"]
        )
        result[0]["items"] = order_lines
        return {"status": 201, "result": result[0]}

    @http.route(
        "/mobile/api/updateOrder",
        methods=["POST"],
        type="json",
        csrf=False,
        auth="public",
    )
    def updateOrder(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "message": "Please Login to Create Order"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        id = kw.get("id")
        update = {}
        address = kw.get("address")
        delivery_time = datetime.fromisoformat(kw.get("deliveryTime"))
        remarks = kw.get("remarks")

        if address:
            update["partner_shipping_id"] = address
        if delivery_time:
            update["expected_delivery_time"] = delivery_time
        if remarks:
            update["customer_note"] = remarks

        partner_id = request.env["res.users"].sudo().browse(user["id"]).partner_id.id
        # partner_id=1
        order = request.env["sale.order"].sudo().search([("id", "=", id)], limit=1)

        if not order:
            return {"status": 404, "message": "order not found", "result": None}

        if order.partner_id.id != partner_id:
            return {
                "status": 403,
                "message": "You are not allowed to edit this order!!",
                "result": None,
            }
        try:
            order.write(update)
            return {"status": 200, "message": "Order updated", "result": None}
        except Exception as e:
            return {"status": 500, "message": "Server Error", "result": None}

    @http.route("/mobile/api/myOrders", type="json", csrf=False, auth="public")
    def myOrders(self, **kw):
        token = request.httprequest.headers.get("Authorization")
        page = kw.get("page") or 1
        limit = 10
        if not token:
            return {"status": 403, "message": "Token Missing"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        partner_id = request.env["res.users"].sudo().browse(user["id"]).partner_id.id
        try:
            total = (
                request.env["sale.order"]
                .sudo()
                .search_count(
                    [
                        ("partner_id", "=", partner_id),
                        ("state", "in", ["sale", "sent", "cancel"]),
                    ]
                )
            )
            orders = (
                request.env["sale.order"]
                .sudo()
                .search_read(
                    [
                        ("partner_id", "=", partner_id),
                        ("state", "in", ["sale", "sent", "cancel"]),
                    ],
                    [
                        "name",
                        "amount_total",
                        "payment_method",
                        "partner_shipping_id",
                        "state",
                        "amount_tax",
                        "amount_untaxed",
                        "order_line",
                        "mobile_delivery_status",
                        "date_order",
                    ],
                    offset=(page - 1) * limit,
                    limit=limit,
                    order="date_order desc",
                )
            )
            for index, order in enumerate(orders):
                order_lines = (
                    request.env["sale.order.line"].sudo().browse(order["order_line"])
                )
                order_lines = order_lines.read(
                    ["product_id", "product_uom_qty", "price_unit"]
                )
                orders[index]["items"] = order_lines
                order["date_order"] = order["date_order"].strftime("%a %B %d %Y")
                order["delivery_to"] = (
                    request.env["res.partner"]
                    .sudo()
                    .browse(order["partner_shipping_id"][0])
                    .street
                )

            return {
                "status": 200,
                "result": {
                    "total": total,
                    "data": orders,
                    "next": page * limit < total,
                },
            }
        except Exception as e:
            return {"status": 500, "result": [], "message": "Something went wrong !!"}

    @http.route("/mobile/api/address", type="json", csrf=False, auth="public")
    def my_address(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "message": "Token Missing"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        partner_id = (
            request.env["res.users"]
            .with_user(SUPERUSER_ID)
            .browse(user["id"])
            .partner_id
        )
        primary = partner_id.read(
            ["name", "street", "type", "phone", "partner_latitude", "partner_longitude"]
        )
        try:
            addresses = partner_id.child_ids.read(
                [
                    "name",
                    "street",
                    "phone",
                    "type",
                    "partner_latitude",
                    "partner_longitude",
                ]
            )
            primary.extend(addresses)
            return {"status": 200, "result": primary}
        except Exception as e:
            print(e)
            return {"status": 500, "result": [], "message": "Something went wrong !!"}

    @http.route("/mobile/api/address/create", type="json", csrf=False, auth="public")
    def create_address(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "message": "Token Missing"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}
        name = kw.get("name")
        street = kw.get("address") or kw.get("street")
        phone = kw.get("phone")

        if name is None or street is None or phone is None:
            return {"status": 400, "message": "Missing Fields !!"}
        partner_id = request.env["res.users"].sudo().browse(user["id"]).partner_id

        try:
            new_address = (
                request.env["res.partner"]
                .sudo()
                .create(
                    {
                        "name": name,
                        "street": street,
                        "phone": phone,
                        "parent_id": partner_id.id,
                        "type": "delivery",
                        "partner_latitude": kw.get("lat") or 0,
                        "partner_longitude": kw.get("long") or 0,
                    }
                )
            )
            return {
                "status": 200,
                "result": new_address.read(["name", "street", "type"])[0],
            }
        except Exception as e:
            # print(e)
            return {"status": 500, "result": [], "message": "Something went wrong !!"}

    @http.route("/mobile/api/address/update", type="json", csrf=False, auth="public")
    def update_address(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "message": "Token Missing"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        id = kw.get("id")
        name = kw.get("name")
        street = kw.get("street") or kw.get("address")
        phone = kw.get("phone")

        if id is None or name is None or street is None or phone is None:
            return {"status": 400, "message": "Missing Fields !!"}

        parent_id = request.env["res.users"].sudo().browse(user["id"]).partner_id.id

        child_id = (
            request.env["res.partner"]
            .with_user(SUPERUSER_ID)
            .search([("id", "=", id)], limit=1)
        )

        if not child_id:
            return {"status": 404, "message": "Address Not Found!!"}

        if child_id.parent_id.id != parent_id:
            return {
                "status": 403,
                "message": "You are not allowed to delete this address !!",
            }

        try:
            child_id.write(
                {
                    "name": name,
                    "street": street,
                    "phone": phone,
                    "partner_latitude": kw.get("lat") or 0,
                    "partner_longitude": kw.get("long") or 0,
                }
            )
            return {"status": 200, "result": None, "message": "Updated"}
        except Exception as e:
            # print(e)
            return {"status": 500, "result": [], "message": "Something went wrong !!"}

    @http.route("/mobile/api/address/delete", type="json", csrf=False, auth="public")
    def delete_address(self, **kw):
        token = request.httprequest.headers.get("Authorization")

        if not token:
            return {"status": 401, "message": "Token Missing"}

        secret_key = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("mobile_sale.secret_key", constant.secret_key)
        )
        user = endoceJwt(token.split(" ")[1], secret_key)

        if not user:
            return {"status": 401, "message": "Token Expired !!"}

        id = kw.get("id")

        if id is None:
            return {"status": 400, "message": "Missing Fields !!"}

        parent_id = request.env["res.users"].sudo().browse(user["id"]).partner_id.id

        child_id = request.env["res.partner"].sudo().search([("id", "=", id)], limit=1)

        if not child_id:
            return {"status": 404, "message": "Address Not Found!!"}

        if child_id.parent_id.id != parent_id:
            return {
                "status": 403,
                "message": "You are not allowed to delete this address !!",
            }

        try:
            child_id.unlink()
            return {"status": 200, "result": None, "message": "Deleted"}
        except Exception as e:
            # print(e)
            return {"status": 500, "result": [], "message": "Something went wrong !!"}


class MobilePayment(PaymentPortal):
    @http.route(
        "/mobile/api/transaction/<int:order_id>",
        type="json",
        auth="public",
    )
    def mobile_payment_transaction(self, order_id, **kwargs):
        order_sudo = request.env["sale.order"].sudo().browse(order_id)

        provider_code = kwargs.get("code")
        # if provider_code == 'esewa':
        #     provider_code = 'esewa-v2'

        provider = (
            request.env["payment.provider"]
            .sudo()
            .search([("code", "=", provider_code)], limit=1)
        )
        # payment_method = request.env['payment.method'].sudo().search([('code','=',kwargs.get('code'))],limit=1)

        _logger.info(provider)
        _logger.info(provider_code)
        if not provider:
            raise ValueError("Provider not found")

        payment_method = provider.payment_method_ids[0]

        del kwargs["code"]
        self._validate_transaction_kwargs(kwargs)
        kwargs.update(
            {
                "partner_id": order_sudo.partner_invoice_id.id,
                "currency_id": order_sudo.currency_id.id,
                "sale_order_id": order_id,
                "provider_id": provider.id,
                "payment_method_id": payment_method.id,
                "token_id": None,
                "flow": "redirect",
                "tokenization_requested": False,
                "landing_route": "/shop/payment/validate",
                "is_validation": False,
                # Include the SO to allow Subscriptions to tokenize the tx
            }
        )
        if not kwargs.get("amount"):
            kwargs["amount"] = order_sudo.amount_total

        tx_sudo = self._create_transaction(
            custom_create_values={"sale_order_ids": [Command.set([order_id])]},
            **kwargs,
        )

        return tx_sudo._get_processing_values()

    @http.route(
        "/mobile/api/poll/SO/<int:year>/<string:sequence>",
        type="json",
        auth="public",
    )
    def mobile_polling(self, year, sequence, **kwargs):
        reference = f"SO/{year}/{sequence}"
        monitored_tx = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference)], limit=1)
        )

        if (
            not monitored_tx
        ):  # The session might have expired, or the tx has never existed.
            return Exception("Tx Not Found !!")

        if not monitored_tx.is_post_processed:
            try:
                monitored_tx._post_process()
            except (
                psycopg2.OperationalError
            ):  # The database cursor could not be committed.
                request.env.cr.rollback()  # Rollback and try later.
                raise Exception("retry")
            except Exception as e:
                request.env.cr.rollback()
                _logger.exception(
                    "Encountered an error while post-processing transaction with id %s:\n%s",
                    monitored_tx.id,
                    e,
                )
                raise

        return {
            "provider_code": monitored_tx.provider_code,
            "state": monitored_tx.state,
            "landing_route": monitored_tx.landing_route,
        }
