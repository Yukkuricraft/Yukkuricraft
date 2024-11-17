#!/usr/bin/env python3

import json

from flask_openapi3 import APIBlueprint  # type: ignore

from flask import request  # type: ignore

from http import HTTPStatus
from datetime import datetime
from pprint import pformat

from src.api import security
from src.api.lib.auth import (
    DuplicateJTIError,
    ExpiredJTIError,
    TimeTravelerError,
    invalidate_access_token,
    prepare_response,
    generate_access_token_if_valid,
    return_cors_response,
    validate_access_token,
    authenticate_access_token,
)
from src.api.lib.helpers import log_request
from src.api.db import db

from src.api.blueprints import (
    auth_tag,
    LoginRequestBody,
    LoginResponse,
    MeResponse,
    UnauthorizedResponse,
)

from src.common.helpers import get_now_dt, log_exception
from src.common.logger_setup import logger

auth_bp: APIBlueprint = APIBlueprint(
    "auth", __name__, url_prefix="/auth", abp_tags=[auth_tag]
)


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
    """Log user in

    `id_token` is expected to be a token string generated via Google's OAuth2 flow.
    If valid, will generate a temporary access token to be used with all of our authenticated endpoints.
    """
    resp = prepare_response()
    resp.status = 401

    logger.debug(">>>>>>>>>>>>>>>>>>")
    logger.debug(resp)
    logger.debug(body)

    access_token = None
    try:
        access_token = generate_access_token_if_valid(body.id_token, db.session)
    except ValueError:
        log_exception(
            message="Got an invalid token!",
            data={
                "token": body.id_token,
            },
        )
    except DuplicateJTIError:
        log_exception()
    except TimeTravelerError:
        log_exception(message="Huh?!")
    except ExpiredJTIError:
        log_exception()

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
    """Logs out for user

    Ends the access token session for the user based on the supplied Auth header
    """
    resp = prepare_response()
    resp.status = 200

    invalidate_access_token(request.headers, db.session)

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
    resp = prepare_response()
    user = authenticate_access_token(request.headers, db.session)
    logger.warning(f"YOU ARE: \n{pformat(user)}")
    if user:
        resp.data = json.dumps(user.to_dict())

    return resp
