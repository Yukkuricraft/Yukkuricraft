#!/usr/bin/env python3

import json

from flask import Blueprint, abort, request  # type: ignore

from datetime import datetime
from pprint import pformat, pprint
from typing import Callable, Dict, Tuple

from src.api.constants import (
    YC_TOKEN_AUTH_SCHEME,
)
from src.api.lib.auth import (
    make_cors_response,
    intercept_cors_preflight,
    generate_access_token_if_valid,
    validate_access_token,
    get_access_token_from_headers,
)
from src.api.lib.helpers import log_request
from src.api.db import db
from src.api.models import AccessToken, User

from src.common.logger_setup import logger

auth_bp: Blueprint = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@log_request
def login_handler():
    if request.method == "POST":
        resp = make_cors_response()
        resp.status = 401

        data = request.get_json()

        logger.warning(">>>>>>>>>>>>>>>>>>")
        logger.warning(resp)
        logger.warning(data)

        access_token = generate_access_token_if_valid(data.get("id_token", None))
        if access_token is not None:
            resp.status = 200
            resp.data = json.dumps({"access_token": access_token})

        return resp


@auth_bp.route("/logout", methods=["OPTIONS", "POST"])
@intercept_cors_preflight
@log_request
def logout_handler():
    if request.method == "POST":
        resp = make_cors_response()
        resp.status = 200

        _, token = get_access_token_from_headers()
        access_token = AccessToken.query.filter_by(id=token).first()
        access_token.exp = int(datetime.now().timestamp())
        db.session.commit()

        return resp


@auth_bp.route("/me", methods=["OPTIONS", "GET"])
@intercept_cors_preflight
@validate_access_token
@log_request
def me_handler():
    if request.method == "GET":
        resp = make_cors_response()
        scheme, access_token = get_access_token_from_headers()
        token = AccessToken.query.filter_by(id=access_token).first()

        logger.warning(f"??? {pformat(token.to_dict())}")

        user = User.query.filter_by(sub=token.user).first()
        logger.warning(f"YOU ARE: \n{pformat(user)}")
        resp.data = json.dumps(user.to_dict())

        return resp
