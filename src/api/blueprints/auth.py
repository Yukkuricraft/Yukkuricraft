#!/usr/bin/env python3

import json

from flask_openapi3 import APIBlueprint  # type: ignore

from http import HTTPStatus
from datetime import datetime
from pprint import pformat

from src.api import security
from src.api.lib.auth import (
    make_cors_response,
    generate_access_token_if_valid,
    return_cors_response,
    validate_access_token,
    get_access_token_from_headers,
)
from src.api.lib.helpers import log_request
from src.api.db import db
from src.api.models import AccessToken, User

from src.api.blueprints import auth_tag, LoginRequestBody, LoginResponse, MeResponse, UnauthorizedResponse

from src.common.logger_setup import logger

auth_bp: APIBlueprint = APIBlueprint("auth", __name__, url_prefix="/auth", abp_tags=[auth_tag])

@auth_bp.route("/login", methods=["OPTIONS"])
@log_request
def login_options_handler():
    return return_cors_response()


@auth_bp.post(
    "/login",
    responses={
        HTTPStatus.OK: LoginResponse,
        HTTPStatus.UNAUTHORIZED: UnauthorizedResponse,
    },
)
@log_request
def login_handler(body: LoginRequestBody):
    """Logs user in and provides a temporary access token for the session.

    `id_token` is expected to be a token string generated via Google's OAuth2 flow.
    If valid, will return a generated access token to be used with all of our authenticated endpoints.
    """
    resp = make_cors_response()
    resp.status = 401

    logger.warning(">>>>>>>>>>>>>>>>>>")
    logger.warning(resp)
    logger.warning(body)

    access_token = generate_access_token_if_valid(body.id_token)
    if access_token is not None:
        resp.status = 200
        resp.data = json.dumps({"access_token": access_token})

    return resp


@auth_bp.route("/logout", methods=["OPTIONS"])
@log_request
def logout_options_handler():
    return return_cors_response()


@auth_bp.post("/logout", security=security)
@log_request
def logout_handler():
    """Logs out of session for user

    Ends the access token session for the user based on the supplied Auth header
    """
    resp = make_cors_response()
    resp.status = 200

    _, token = get_access_token_from_headers()
    access_token = AccessToken.query.filter_by(id=token).first()
    access_token.exp = int(datetime.now().timestamp())
    db.session.commit()

    return resp


@auth_bp.route("/me", methods=["OPTIONS"])
@log_request
def me_options_handler():
    return return_cors_response()


@auth_bp.get(
    "/me",
    security=security,
    responses={
        HTTPStatus.OK: MeResponse,
        HTTPStatus.UNAUTHORIZED: UnauthorizedResponse,
    },
)
@validate_access_token
@log_request
def me_handler():
    """Identity validation endpoint

    Returns a 2xx/4xx depending on if a request was made with a valid JWT token in the header.
    """
    resp = make_cors_response()
    _scheme, access_token = get_access_token_from_headers()
    token = AccessToken.query.filter_by(id=access_token).first()

    logger.warning(f"??? {pformat(token.to_dict())}")

    user = User.query.filter_by(sub=token.user).first()
    logger.warning(f"YOU ARE: \n{pformat(user)}")
    resp.data = json.dumps(user.to_dict())

    return resp
