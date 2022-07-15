#!/usr/bin/env python3
from pprint import pformat, pprint

from flask import Blueprint, request, make_response
from flask_restx import Api, Resource, abort, fields, reqparse  # type: ignore

from datetime import datetime
from functools import wraps
from google.oauth2 import id_token  # type: ignore
from google.auth.transport import requests as g_requests  # type: ignore
from typing import Callable, Dict

from src.api.constants import G_CLIENT_ID
from src.api.constants import CORS_ORIGIN
from src.api.db import db
from src.api.models import User, JTI, create_db_tables


from logging import getLogger

logger = getLogger(__name__)


class DuplicateJTIError(RuntimeError):
    msg = "Duplicate JTI was used!"

    def __init__(self, idinfo: Dict):
        self.idinfo = idinfo

        super().__init__(f"{self.msg}\n{pformat(self.idinfo)}")


class ExpiredJTIError(RuntimeError):
    def __init__(self, exp_dt: datetime, now: datetime):
        super().__init__(f"Token expired at {exp_dt}! currently {now}")


class TimeTravelerError(RuntimeError):
    msg = "Go back to the shadow from whence you came!"

    def __init__(self, iat_dt: datetime):
        now_dt = datetime.now()
        super().__init__(
            f"{self.msg}\n"
            f"iat_ts: {int(iat_dt.timestamp())}\n"
            f"now_ts: {int(now_dt.timestamp())}\n"
            f"iat_dt: {iat_dt}\n"
            f"now_dt: {now_dt}\n"
        )


def verify_id_token_allowed(token: str):
    try:
        idinfo = id_token.verify_oauth2_token(token, g_requests.Request(), G_CLIENT_ID)

        logger.debug(pformat(idinfo))

        jti, exp, iat, sub, email = (
            idinfo["jti"],
            idinfo["exp"],
            idinfo["iat"],
            idinfo["sub"],
            idinfo["email"],
        )

        exp_dt = datetime.utcfromtimestamp(exp)
        iat_dt = datetime.utcfromtimestamp(iat)

        now = datetime.now()

        if JTI.query.filter_by(jti=jti).first():
            raise DuplicateJTIError(idinfo)
        elif now >= exp_dt:
            raise ExpiredJTIError(exp_dt, now)
        elif now <= iat_dt:
            raise TimeTravelerError(iat_dt)

        user = User(sub=sub, email=email)
        if not User.query.filter_by(sub=sub).first():
            db.session.add(user)
        db.session.add(JTI(jti=jti, exp=exp, iat=iat, user=user.sub))
        db.session.commit()

        return True
    except ValueError as e:
        logger.warning("Got an invalid idtoken?")
        logger.warning(f"Token: {token}")
    except DuplicateJTIError as e:
        logger.warning(e)
    except TimeTravelerError as e:
        logger.warning("Huh?!")
        logger.warning(e)
    except ExpiredJTIError as e:
        logger.warning(e)

    return False


def req_https(func: Callable):
    if not request.is_secure:
        abort(401)


def req_google_id_whitelist(func: Callable):
    post_data = request.get_json()
    token = ""
    if not verify_id_token_allowed(token):
        abort(401)
        pass


def _add_yakumo_cors_response():
    response = make_response()
    if request.method == "OPTIONS":
        response.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response

    elif request.method == "POST":
        response.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)
        return response

    else:
        raise Exception(
            f"Tried adding CORS headers to invalid request type. Got: '{request.method}'"
        )


auth_blueprint: Blueprint = Blueprint("auth", __name__)
auth_api: Api = Api(auth_blueprint)

LoginReqArgs = reqparse.RequestParser()
LoginReqArgs.add_argument(
    "id_token", type=str, required=True, help="Must pass id_token to authenticate as"
)


@auth_api.route("/login")
class Login(Resource):
    def options(self):
        return _add_yakumo_cors_response()

    @auth_api.doc("Log in with id_token")
    def post(self):
        resp = _add_yakumo_cors_response()
        resp.status = 401

        data = LoginReqArgs.parse_args()

        logger.info(">>>>>>>>>>>>>>>>>>")
        logger.info(resp)
        logger.info(data)

        if verify_id_token_allowed(data.id_token):
            resp.status = 200

        return resp


# @auth_api.route("/createdbdeleteme")
class CreateDB(Resource):
    def get(self):
        create_db_tables()
        return "Aaaa"
