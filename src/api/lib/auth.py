from flask_sqlalchemy.session import Session
from sqlalchemy.orm import scoped_session  # type: ignore

from flask import request, make_response, Response, current_app  # type: ignore

from urllib.parse import urlparse, parse_qsl

from pprint import pformat
from functools import wraps
from typing import Any, Dict, Optional, Tuple, Callable
from datetime import datetime, timezone
from secrets import token_hex
from google.oauth2 import id_token  # type: ignore
from google.auth.transport import requests as g_requests  # type: ignore
from uuid import uuid4


from src.api.constants import (
    IS_LOCAL,
    ACCESS_TOKEN_DUR_MINS,
    G_CLIENT_ID,
    CORS_ORIGIN,
    WHITELISTED_USERS_FILE,
    YC_TOKEN_AUTH_SCHEME,
)
from src.api.db import db
from src.api.models import AccessToken, User, JTI

from src.common.helpers import get_now_dt, log_exception
from src.common.logger_setup import logger

# TODO: Make more sophisticated in the future but for now this suffices.
WHITELISTED_USERS = set(open(WHITELISTED_USERS_FILE, "r").read().splitlines())

## Custom Errors


class InvalidTokenError(RuntimeError):
    msg = "Got an invalid token that we could not inspect!"

    def __init__(self, token: Any):
        self.token = token
        super().__init__(f"{self.msg}\n'{pformat(self.token)}'")


class InvalidTokenSchemeError(RuntimeError):
    msg = "Got an invalid token scheme!"

    def __init__(self, scheme: Optional[str] = None):
        self.scheme = scheme
        super().__init__(f"{self.msg} - Got '{self.scheme}'")


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
        now_dt = get_now_dt()
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
    return token_hex(), (int(get_now_dt().timestamp()) + 60 * ACCESS_TOKEN_DUR_MINS)


def deserialize_id_token(token: str) -> Dict:
    """Deserializes the oauth token

    Args:
        token (str): JWT token generated from OAuth2

    Returns:
        Dict: JWT token deserialized as a dict
    """
    if IS_LOCAL:
        # Local dev bypasses google oauth so we have a non-sensical `token` value. Just make shit up.
        return {
            "jti": uuid4().hex,
            "exp": 1999999999,
            "iat": int(get_now_dt().strftime("%s")),
            "sub": "123456789012345678901",
            "email": "local@development.yc",
        }
    return id_token.verify_oauth2_token(token, g_requests.Request(), G_CLIENT_ID)


def get_access_token_from_headers(headers: Dict[str, str]) -> Tuple[str, str]:
    """Helper to get the scheme and token of the `Authorization` header from a flask request.

    Header will usually look like: `Authorization: {scheme} {token}`

    If no auth header is found, will fall back to attempting querystring based authorization for websocket auth.

    Returns:
        Tuple[str, str]: Scheme and token
    """
    # Authorization: Bearer <access_token>
    auth_header = headers.get("Authorization", "")

    logger.info(f"auth_header: {auth_header}")
    if auth_header:
        scheme, token = auth_header.split()
        return scheme, token

    return get_auth_string_from_websocket_request(headers)


def get_auth_string_from_websocket_request(headers: Dict[str, str]) -> Tuple[str, str]:
    """Helper to get token of the `Authorization` query string from a flask request.

    Used for websocket auth as websockets do not allow arbitrary headers such as `Authorization:` to be added

    Expects to be used behind an nginx auth_request subrequest with the original uri passed as an X-Original-Uri header

    Unlike with the `Authorization:` header, we do not expect a token scheme for querystring authorization. Instead we pass back a hardcoded scheme of `Bearer` for compatibility.


    Returns:
        Tuple[str, str]: Scheme and token
    """

    x_original_uri_header = headers.get(
        "X-Original-Uri", ""
    )  # Expected to be passed from nginx reverse proxy
    if not x_original_uri_header:
        raise InvalidTokenError("No auth header or proxy uri header set!")

    parsed_url = urlparse(x_original_uri_header)
    querystring_dict = dict(parse_qsl(parsed_url.query))

    auth_token = querystring_dict.get("Authorization", "")
    if not auth_token:
        raise InvalidTokenError(
            "Found valid proxy uri header but no authorization token!"
        )

    return "Bearer", auth_token


def generate_access_token_if_valid(
    token: str, session: scoped_session[Session]
) -> Optional[str]:
    """Validates the oauth token string, which encodes info like the subject, email, jti, etc, and generates a temporary access token if valid.

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

    idinfo = deserialize_id_token(token)

    logger.debug(pformat(idinfo))

    jti, exp, iat, sub, email = (
        idinfo["jti"],
        idinfo["exp"],
        idinfo["iat"],
        idinfo["sub"],
        idinfo["email"],
    )

    user = User(sub=sub, email=email)
    exp_dt = datetime.fromtimestamp(exp, timezone.utc)
    iat_dt = datetime.fromtimestamp(iat, timezone.utc)

    now = get_now_dt()

    logger.info(pformat([user, exp_dt, exp, iat_dt, iat, now]))
    if session.query(JTI).filter(JTI.jti == jti).first():
        raise DuplicateJTIError(idinfo)
    elif now >= exp_dt:
        raise ExpiredJTIError(exp_dt, now)
    elif now <= iat_dt:
        raise TimeTravelerError(iat_dt)
    elif sub not in WHITELISTED_USERS:
        raise UnknownUserError(user)

    access_token, access_token_exp = generate_access_token()
    if not session.query(User).filter(User.sub == sub).first():
        session.add(user)
    session.add(JTI(jti=jti, exp=exp, iat=iat, user=user.sub))
    session.add(AccessToken(id=access_token, user=user.sub, exp=access_token_exp))
    session.commit()

    return access_token


def verify_access_token_allowed(
    scheme: str, access_token: str, session: scoped_session[Session]
):
    """Verifies we issued the access token by checking the DB

    Args:
        scheme (str): The token scheme. We expect it to match `YC_TOKEN_AUTH_SCHEME`
        access_token (str): Token to verify

    Raises:
        InvalidTokenError: If token could not be parsed
        ExpiredJTIError: If token is expired
        InvalidTokenSchemeError: If scheme doesn't match `YC_TOKEN_AUTH_SCHEME`

    """
    token = session.query(AccessToken).filter(AccessToken.id == access_token).first()
    now = get_now_dt()

    if not token:
        raise InvalidTokenError(token)
    elif now >= datetime.fromtimestamp(token.exp, timezone.utc):
        raise ExpiredJTIError(token.exp, now)
    elif scheme != YC_TOKEN_AUTH_SCHEME:
        raise InvalidTokenSchemeError(scheme)


def validate_access_token(func_to_decorate: Callable):
    """Decorator for validating Flask request has a valid access token in its headers

    Args:
        func (Callable): Function to be decorated.

    Returns:
        Callable: Decorated function
    """

    @wraps(func_to_decorate)
    def decorated_function(*args, **kwargs):
        unauthed_resp = prepare_response()
        unauthed_resp.status = 401
        try:
            scheme, token = get_access_token_from_headers(request.headers)
            logger.warning(f"INSPECTING AUTH HEADER: '{scheme}' '{token}'")
            verify_access_token_allowed(scheme, token, db.session)
        except Exception as e:
            log_exception()
            return unauthed_resp

        return func_to_decorate(*args, **kwargs)

    return decorated_function


def authenticate_access_token(
    headers: Dict, session: scoped_session[Session]
) -> Optional[User]:
    """If a valid access token is found, returns the user that it was issued for.

    Validity of the access token must be checked separately using the `@validate_access_token` decorator.

    Args:
        headers (Dict): Request headers
        session (sqlalchemy.orm.session): Database session used to read persisted token and user data.

    Returns:
        Optional[User]: If the access token was found, returns the user it was issued for.
    """
    _scheme, access_token = get_access_token_from_headers(headers)
    token = session.query(AccessToken).filter(AccessToken.id == access_token).first()
    if not token:
        return None
    user = session.query(User).filter(User.sub == token.user).first()
    return user


def invalidate_access_token(headers: Dict, session: scoped_session[Session]):
    """Expires the access token found in the headers.

    Args:
        headers (Dict): Request headers
        session (sqlalchemy.orm.session): Database session for persisting token expiration.
    """
    _, token = get_access_token_from_headers(headers)
    access_token = session.query(AccessToken).filter(AccessToken.id == token).first()
    if access_token is not None:
        access_token.exp = int(get_now_dt().timestamp())
    session.commit()


def return_cors_response() -> Response:
    """Makes a skeleton Flask Response with CORS headers.

    Returns:
        flask.Response: Response object with only the CORS headers set.
    """
    resp = make_response()
    resp.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)
    resp.headers.add("Access-Control-Allow-Headers", "*")
    resp.headers.add("Access-Control-Allow-Methods", "*")

    return resp


def prepare_response(status_code=200):
    """Helper for creating an empty response object with the CORS origin and other headers added.

    Args:
        status_code (int, optional): Status code of the response. Defaults to 200.

    Returns:
        Flask response object
    """
    resp = make_response("")

    resp.headers.add("Access-Control-Allow-Origin", CORS_ORIGIN)
    resp.content_type = "application/json"
    resp.status = status_code

    return resp
