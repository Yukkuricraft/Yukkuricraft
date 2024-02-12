from flask import request, make_response, current_app  # type: ignore

from pprint import pformat
from functools import wraps
from typing import Dict, Optional, Tuple, Callable
from datetime import datetime
from secrets import token_hex
from google.oauth2 import id_token  # type: ignore
from google.auth.transport import requests as g_requests  # type: ignore


from src.api.constants import (
    ACCESS_TOKEN_DUR_MINS,
    G_CLIENT_ID,
    CORS_ORIGIN,
    WHITELISTED_USERS_FILE,
    YC_TOKEN_AUTH_SCHEME,
)
from src.api.db import db
from src.api.models import AccessToken, User, JTI, create_db_tables

from src.common.logger_setup import logger

# TODO: Make more sophisticated in the future but for now this suffices.
WHITELISTED_USERS = set(open(WHITELISTED_USERS_FILE, "r").read().splitlines())

## Custom Errors


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


class UnknownUserError(RuntimeError):
    msg = "Encountered valid login but user was not whitelisted."

    def __init__(self, user: User):
        super().__init__(pformat(user))


class UnknownAccessTokenError(RuntimeError):
    def __init__(self, access_token: str):
        super().__init__(f"Got unknown access token: '{access_token}'")


class ExpiredAccessTokenError(RuntimeError):
    def __init__(self, token: AccessToken):
        super().__init__(f"Got expired token: {token.id}\nExpired at: {token.exp}")


## Funcs


def generate_access_token() -> Tuple[str, int]:
    """Generates a random token and its expiration

    Returns:
        Tuple[str, int]: _description_
    """
    return token_hex(), (int(datetime.now().timestamp()) + 60 * ACCESS_TOKEN_DUR_MINS)


def deserialize_id_token(token: str) -> Dict:
    """Deserializes the oauth token

    Args:
        token (str): _description_

    Returns:
        Dict: _description_
    """
    return id_token.verify_oauth2_token(token, g_requests.Request(), G_CLIENT_ID)


def get_access_token_from_headers() -> Tuple[str, str]:
    """Helper to get the scheme and token of the `Authorization` header from a flask request.

    Header will usually look like: `Authorization: {scheme} {token}`

    Returns:
        Tuple[str, str]: Scheme and token
    """
    # Authorization: YC-Token <access_token>
    auth_header = request.headers.get("Authorization", "")
    scheme, token = auth_header.split()

    return scheme, token


def generate_access_token_if_valid(token: str) -> Optional[str]:
    """Validates the oauth token string, which encodes info like the subject, email, jti, etc, and generated a temporary access token if valid.
a
    Args:
        token (str): Token string

    Raises:
        DuplicateJTIError: If the we've seen this unique JTI already before. Duplicate requests?
        ExpiredJTIError: If the decoded JTI has expired
        TimeTravelerError: If the decoded iat (issued at time) is somehow in the future
        UnknownUserError: If the decoded subject is not whitelisted

    Returns:
        Optional[str]: None if provided `token` was invalid. Otherwise the generated access token as a string.
    """
    try:
        idinfo = deserialize_id_token(token)

        logger.debug(pformat(idinfo))

        jti, exp, iat, sub, email = (
            idinfo["jti"],
            idinfo["exp"],
            idinfo["iat"],
            idinfo["sub"],
            idinfo["email"],
        )

        logger.info(idinfo)

        user = User(sub=sub, email=email)
        exp_dt = datetime.utcfromtimestamp(exp)
        iat_dt = datetime.utcfromtimestamp(iat)

        now = datetime.now()

        if JTI.query.filter_by(jti=jti).first():
            raise DuplicateJTIError(idinfo)
        elif now >= exp_dt:
            raise ExpiredJTIError(exp_dt, now)
        elif now <= iat_dt:
            raise TimeTravelerError(iat_dt)
        elif sub not in WHITELISTED_USERS:
            raise UnknownUserError(user)

        access_token, access_token_exp = generate_access_token()
        if not User.query.filter_by(sub=sub).first():
            db.session.add(user)
        db.session.add(JTI(jti=jti, exp=exp, iat=iat, user=user.sub))
        db.session.add(
            AccessToken(id=access_token, user=user.sub, exp=access_token_exp)
        )
        db.session.commit()

        return access_token
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

    return None



def verify_access_token_allowed(access_token: str):
    """Verifies we issued the access token by checking the DB

    Args:
        access_token (str): Token to verify

    Returns:
        _type_: _description_
    """
    token = AccessToken.query.filter_by(id=access_token).first()

    if not token:
        logger.warning(pformat(token))
        logger.warning("Unknown Token")
        return False
    elif datetime.now() >= datetime.utcfromtimestamp(token.exp):
        logger.warning(token.exp)
        logger.warning("Expired token")
        return False

    return True


def validate_access_token(func: Callable):
    """Decorator for validating Flask request has a valid access token in its headers

    Args:
        func (Callable): Function to be decorated.

    Returns:
        Callable: Decorated function
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        unauthed_resp = make_cors_response()
        unauthed_resp.status = 401
        try:
            scheme, token = get_access_token_from_headers()
            logger.warning(f"INSPECTING AUTH HEADER: '{scheme}' '{token}'")

            if scheme != YC_TOKEN_AUTH_SCHEME:
                return unauthed_resp
            elif not verify_access_token_allowed(token):
                return unauthed_resp
        except Exception as e:
            logger.warning(e)
            return unauthed_resp

        return func(*args, **kwargs)

    return decorated_function


def intercept_cors_preflight(func: Callable):
    """Decorator for flask endpoints that injects CORS origin headers into any OPTIONS requests

    Args:
        func (Callable): Function to be decorated.

    Returns:
        Callable: Decorated function
    """
    @wraps(func)
    def decorated_function(*args, **kwargs):
        # logger.info(request.method)
        if request.method == "OPTIONS":
            resp = make_response()
            resp.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)
            resp.headers.add("Access-Control-Allow-Headers", "*")
            resp.headers.add("Access-Control-Allow-Methods", "*")

            # logger.info(f"RETURNING INTERCEPTED CORS PREFLIGHT:")
            # logger.info(pformat(resp))
            return resp

        return func(*args, **kwargs)

    return decorated_function


def make_cors_response(status_code=200):
    """Helper for creating an empty response object with the CORS origin headers added.

    Args:
        status_code (int, optional): Status code of the response. Defaults to 200.

    Returns:
        Flask response object
    """
    resp = make_response("", status_code)
    resp.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)
    return resp
