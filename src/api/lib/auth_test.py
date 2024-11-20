from datetime import datetime, timezone
from uuid import uuid4
from unittest import mock

import pytest  # type: ignore
import flask  # type: ignore

from mock_alchemy.mocking import UnifiedAlchemyMagicMock
from pytest_mock import MockerFixture  # type: ignore

from src.api.lib.auth import (
    DuplicateJTIError,
    ExpiredJTIError,
    InvalidTokenError,
    InvalidTokenSchemeError,
    TimeTravelerError,
    UnknownUserError,
    generate_access_token,
    deserialize_id_token,
    generate_access_token_if_valid,
    get_access_token_from_headers,
    get_auth_string_from_websocket_request,
    prepare_response,
    validate_access_token,
    verify_access_token_allowed,
)
from src.api.models import JTI, AccessToken

from src.common.logger_setup import logger


@pytest.fixture
def jti():
    return uuid4().hex


@pytest.fixture
def sub():
    return "testtesttesttesttest"


@pytest.fixture
def email():
    return "test@development.yc"


@pytest.fixture
def iat():
    return int(datetime.now(timezone.utc).strftime("%s"))


@pytest.fixture
def exp():
    return 1999999999


@pytest.fixture
def now():
    return 2999999999


@pytest.fixture
def jwt_object(jti, exp, iat, sub, email):
    return {
        "jti": jti,
        "exp": exp,
        "iat": iat,
        "sub": sub,
        "email": email,
    }


@pytest.fixture
def expected_token():
    return "foobar-123"


@pytest.fixture
def expected_scheme():
    return "Bearer"


@pytest.fixture
def unexpected_scheme():
    return "NotBearer"


@pytest.fixture
def bogus_token():
    return "bogus-token"


@pytest.fixture
def mocked_email():
    return "mocked@email.com"


class TestAuth:
    """Auth lib unit tests"""

    def test__generate_access_token__success(self):
        """Validate we're able to generate a valid access token."""
        # EXECUTE
        token_hex, expiration = generate_access_token()

        # ASSERT
        assert isinstance(token_hex, str), "Expected token hex to be a str!"
        assert isinstance(expiration, int), "Expected expiration to be an int!"

    def test__deserialize_id_token__local(self, mocker: MockerFixture, bogus_token):
        """If IS_LOCAL is True, make sure we're returning our hardcoded bypass token dict."""
        # SETUP
        mocker.patch("src.api.lib.auth.IS_LOCAL", True)

        # EXECUTE
        d = deserialize_id_token(bogus_token)

        # ASSERT
        assert (
            d["email"] == "local@development.yc"
        ), "Expected local mode to always return 'local@development.yc' for email!"

    def test__deserialize_id_token__not_local(
        self, mocker: MockerFixture, mocked_email, bogus_token
    ):
        """If IS_LOCAL is False, make sure we're calling google's oauth token verify function"""
        # SETUP
        mocker.patch("src.api.lib.auth.IS_LOCAL", False)
        mocker.patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={"email": mocked_email},
        )

        # EXECUTE
        d = deserialize_id_token(bogus_token)

        # ASSERT
        assert (
            d["email"] == mocked_email
        ), "Expected non-local mode to return mocked email from verify_oauth2_token!"

    def test__get_access_token_from_headers__auth_header(
        self, expected_scheme, expected_token
    ):
        """Validate access_token is returned from the auth header"""
        # EXECUTE
        scheme, token = get_access_token_from_headers(
            headers={"Authorization": f"{expected_scheme} {expected_token}"}
        )

        # ASSERT
        assert scheme == expected_scheme, f"Expected scheme to be '{expected_scheme}'!"
        assert token == expected_token, f"Expected token to be '{expected_token}'!"

    def test__get_access_token_from_headers__x_uri_header(self, mocker):
        """Validate that if the auth token is not in the `Authorization` header, we properly fall back to checkign the X-Original-Uri header."""
        # SETUP
        import src.api.lib.auth

        spy = mocker.spy(src.api.lib.auth, "get_auth_string_from_websocket_request")

        # EXECUTE
        get_access_token_from_headers(
            headers={"X-Original-Uri": f"stuff/at/path?Authorization=anystring"}
        )

        # ASSERT
        assert (
            spy.call_count == 1
        ), f"Expected src.api.lib.auth.get_auth_string_from_websocket_request() to get called once!"

    def test__get_auth_string_from_websocket_request__success(
        self, expected_scheme, expected_token
    ):
        # EXECUTE
        scheme, token = get_auth_string_from_websocket_request(
            headers={"X-Original-Uri": f"stuff/at/path?Authorization={expected_token}"}
        )

        # ASSERT
        assert scheme == expected_scheme, f"Expected scheme to be '{expected_scheme}'!"
        assert token == expected_token, f"Expected token to be '{expected_token}'!"

    def test__generate_access_token_if_valid__duplicate_jti_error(
        self, mocker: MockerFixture, jti, bogus_token, jwt_object
    ):
        # SETUP
        mocker.patch("src.api.lib.auth.deserialize_id_token", return_value=jwt_object)

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [mock.call.query(JTI), mock.call.filter(JTI.jti == jti)],
                    [JTI(jti=jti)],
                )
            ]
        )

        with pytest.raises(DuplicateJTIError):
            # EXECUTE
            # ASSERT
            generate_access_token_if_valid(bogus_token, session)

    def test__generate_access_token_if_valid__expired_jti_error(
        self, mocker: MockerFixture, exp, bogus_token, jwt_object
    ):
        # SETUP
        mocker.patch("src.api.lib.auth.deserialize_id_token", return_value=jwt_object)
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(exp + 1, timezone.utc),
        )

        with pytest.raises(ExpiredJTIError):
            # EXECUTE
            # ASSERT
            generate_access_token_if_valid(bogus_token, UnifiedAlchemyMagicMock())

    def test__generate_access_token_if_valid__time_traveler_error(
        self, mocker: MockerFixture, iat, bogus_token, jwt_object
    ):
        # SETUP
        mocker.patch("src.api.lib.auth.deserialize_id_token", return_value=jwt_object)
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(iat - 1, timezone.utc),
        )

        with pytest.raises(TimeTravelerError):
            # EXECUTE
            # ASSERT
            generate_access_token_if_valid(bogus_token, UnifiedAlchemyMagicMock())

    def test__generate_access_token_if_valid__unknown_user_error(
        self, mocker: MockerFixture, iat, bogus_token, jwt_object
    ):
        # SETUP
        mocker.patch("src.api.lib.auth.deserialize_id_token", return_value=jwt_object)
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(iat + 1, timezone.utc),
        )

        with pytest.raises(UnknownUserError):
            # EXECUTE
            # ASSERT
            generate_access_token_if_valid(bogus_token, UnifiedAlchemyMagicMock())

    def test__generate_access_token_if_valid__success(
        self, mocker: MockerFixture, iat, sub, bogus_token, jwt_object, expected_token
    ):
        # SETUP
        mocker.patch("src.api.lib.auth.deserialize_id_token", return_value=jwt_object)
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(iat + 1, timezone.utc),
        )
        mocker.patch("src.api.lib.auth.WHITELISTED_USERS", [sub])
        mocker.patch(
            "src.api.lib.auth.generate_access_token",
            return_value=(expected_token, iat + 9999),
        )

        # EXECUTE
        token = generate_access_token_if_valid(bogus_token, UnifiedAlchemyMagicMock())

        # ASSERT
        assert (
            token == expected_token
        ), f"Did not get the expected access token value '{expected_token}'!"

    def test__verify_access_token_allowed__invalid_token_error(
        self, expected_scheme, expected_token
    ):
        # SETUP
        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == expected_token),
                    ],
                    [],
                )
            ]
        )
        with pytest.raises(InvalidTokenError):
            # EXECUTE
            # ASSERT
            verify_access_token_allowed(expected_scheme, expected_token, session)

    def test__verify_access_token_allowed__expired_jti_error(
        self, mocker: MockerFixture, expected_scheme, expected_token, exp
    ):
        # SETUP
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(exp + 1, timezone.utc),
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == expected_token),
                    ],
                    [AccessToken(id=expected_token, exp=exp)],
                )
            ]
        )
        with pytest.raises(ExpiredJTIError):
            # EXECUTE
            # ASSERT
            verify_access_token_allowed(expected_scheme, expected_token, session)

    def test__verify_access_token_allowed__invalid_token_scheme_error(
        self, mocker: MockerFixture, unexpected_scheme, expected_token, exp
    ):
        # SETUP
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(exp - 1, timezone.utc),
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == expected_token),
                    ],
                    [AccessToken(id=expected_token, exp=exp)],
                )
            ]
        )
        with pytest.raises(InvalidTokenSchemeError):
            # EXECUTE
            # ASSERT
            verify_access_token_allowed(unexpected_scheme, expected_token, session)

    def test__verify_access_token_allowed__success(
        self, mocker: MockerFixture, expected_scheme, expected_token, exp
    ):
        # SETUP
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(exp - 1, timezone.utc),
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == expected_token),
                    ],
                    [AccessToken(id=expected_token, exp=exp)],
                )
            ]
        )

        # EXECUTE
        try:
            verify_access_token_allowed(expected_scheme, expected_token, session)
        except Exception as e:
            # ASSERT
            pytest.fail(
                f"Got an exception when not expected! Got a '{type(e).__name__}'"
            )

    def test__validate_access_token__unauthorized(
        self, mocker: MockerFixture, expected_token, now
    ):
        # SETUP
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(now, timezone.utc),
        )
        mocker.patch(
            "src.api.lib.auth.get_access_token_from_headers",
            return_value=("Bearer", expected_token),
        )
        mocker.patch("src.api.lib.auth.make_response", return_value=flask.Response())
        verify_token_mock = mocker.patch("src.api.lib.auth.verify_access_token_allowed")
        verify_token_mock.side_effect = InvalidTokenError("")

        # EXECUTE
        val = validate_access_token(lambda: prepare_response(200))()

        # ASSERT
        assert val.status_code == 401, "Expected to get a 401 unauthoritzed!"

    def test__validate_access_token__authorized(
        self, mocker: MockerFixture, expected_token, now
    ):
        # SETUP
        mocker.patch(
            "src.api.lib.auth.get_now_dt",
            return_value=datetime.fromtimestamp(now, timezone.utc),
        )
        mocker.patch(
            "src.api.lib.auth.get_access_token_from_headers",
            return_value=("Bearer", expected_token),
        )
        mocker.patch("src.api.lib.auth.make_response", return_value=flask.Response())
        mocker.patch("src.api.lib.auth.verify_access_token_allowed", return_value=None)

        mock_request = mocker.MagicMock()
        mock_request.headers = {"Authorization": "Bearer test__token"}
        mocker.patch("src.api.lib.auth.request", mock_request)

        # EXECUTE
        val = validate_access_token(lambda: prepare_response(200))()

        # ASSERT
        assert val.status_code == 200, "Expected to get a 200 authorized!"
