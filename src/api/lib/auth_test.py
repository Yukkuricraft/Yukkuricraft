from datetime import datetime, timezone
from uuid import uuid4
from unittest import mock

import pytest  # type: ignore
import flask  # type: ignore

from mock_alchemy.mocking import UnifiedAlchemyMagicMock  # type: ignore

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

jti = uuid4().hex
exp = 1999999999
iat = int(datetime.now(timezone.utc).strftime("%s"))
sub = "testtesttesttesttest"
email = "test@development.yc"


class TestAuth:
    jwt_object = {
        "jti": jti,
        "exp": exp,
        "iat": iat,
        "sub": sub,
        "email": email,
    }

    def test_generate_access_token(self):
        """Validate we're able to generate a valid access token."""
        token_hex, expiration = generate_access_token()
        assert isinstance(token_hex, str), "Expected token hex to be a str!"
        assert isinstance(expiration, int), "Expected expiration to be an int!"

    def test_deserialize_id_token_local(self, mocker):
        """If IS_LOCAL is True, make sure we're returning our hardcoded bypass token dict."""
        token = "bogus-token"
        mocker.patch("src.api.lib.auth.IS_LOCAL", True)

        d = deserialize_id_token(token)
        assert (
            d["email"] == "local@development.yc"
        ), "Expected local mode to always return 'local@development.yc' for email!"

    def test_deserialize_id_token_notlocal(self, mocker):
        """If IS_LOCAL is False, make sure we're calling google's oauth token verify function"""
        mocked_email = "mocked@email.com"
        token = "bogus-token"

        mocker.patch("src.api.lib.auth.IS_LOCAL", False)
        mocker.patch(
            "google.oauth2.id_token.verify_oauth2_token",
            return_value={"email": mocked_email},
        )

        d = deserialize_id_token(token)
        assert (
            d["email"] == mocked_email
        ), "Expected non-local mode to return mocked email from verify_oauth2_token!"

    def test_get_access_token_from_headers_auth_header(self):
        """Validate access_token is returned from the auth header"""
        expected_scheme = "Bearer"
        expected_token = "abcfoobar123"

        scheme, token = get_access_token_from_headers(
            headers={"Authorization": f"{expected_scheme} {expected_token}"}
        )

        assert scheme == expected_scheme, f"Expected scheme to be '{expected_scheme}'!"
        assert token == expected_token, f"Expected token to be '{expected_token}'!"

    def test_get_access_token_from_headers_x_uri_header(self, mocker):
        """Validate that if the auth token is not in the `Authorization` header, we properly fall back to checkign the X-Original-Uri header."""

        import src.api.lib.auth

        spy = mocker.spy(src.api.lib.auth, "get_auth_string_from_websocket_request")

        get_access_token_from_headers(
            headers={"X-Original-Uri": f"stuff/at/path?Authorization=anystring"}
        )

        assert (
            spy.call_count == 1
        ), f"Expected src.api.lib.auth.get_auth_string_from_websocket_request() to get called once!"

    def test_get_auth_string_from_websocket_request(self):

        expected_scheme = "Bearer"
        expected_token = "abcfoobar123"

        scheme, token = get_auth_string_from_websocket_request(
            headers={"X-Original-Uri": f"stuff/at/path?Authorization={expected_token}"}
        )

        assert scheme == expected_scheme, f"Expected scheme to be '{expected_scheme}'!"
        assert token == expected_token, f"Expected token to be '{expected_token}'!"

    def test_generate_access_token_if_valid_duplicate_jti_error(self, mocker):
        mocker.patch(
            "src.api.lib.auth.deserialize_id_token", return_value=self.jwt_object
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [mock.call.query(JTI), mock.call.filter(JTI.jti == jti)],
                    [JTI(jti=jti)],
                )
            ]
        )

        with pytest.raises(DuplicateJTIError):
            generate_access_token_if_valid("bogus-token", session)

    def test_generate_access_token_if_valid_expired_jti_error(self, mocker):
        mocker.patch(
            "src.api.lib.auth.deserialize_id_token", return_value=self.jwt_object
        )
        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(exp + 1, timezone.utc),
        )

        with pytest.raises(ExpiredJTIError):
            generate_access_token_if_valid("bogus-token", UnifiedAlchemyMagicMock())

    def test_generate_access_token_if_valid_time_traveler_error(self, mocker):
        mocker.patch(
            "src.api.lib.auth.deserialize_id_token", return_value=self.jwt_object
        )
        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(iat - 1, timezone.utc),
        )

        with pytest.raises(TimeTravelerError):
            generate_access_token_if_valid("bogus-token", UnifiedAlchemyMagicMock())

    def test_generate_access_token_if_valid_unknown_user_error(self, mocker):
        mocker.patch(
            "src.api.lib.auth.deserialize_id_token", return_value=self.jwt_object
        )
        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(iat + 1, timezone.utc),
        )

        with pytest.raises(UnknownUserError):
            generate_access_token_if_valid("bogus-token", UnifiedAlchemyMagicMock())

    def test_generate_access_token_if_valid(self, mocker):
        expected_access_token = "foobar-123"

        mocker.patch(
            "src.api.lib.auth.deserialize_id_token", return_value=self.jwt_object
        )
        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(iat + 1, timezone.utc),
        )
        mocker.patch("src.api.lib.auth.WHITELISTED_USERS", [sub])
        mocker.patch(
            "src.api.lib.auth.generate_access_token",
            return_value=(expected_access_token, iat + 9999),
        )

        token = generate_access_token_if_valid("bogus-token", UnifiedAlchemyMagicMock())

        assert (
            token == expected_access_token
        ), f"Did not get the expected access token value '{expected_access_token}'!"

    def test_verify_access_token_allowed_invalid_token_error(self):
        scheme = "Bearer"
        token = "abc123"
        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == token),
                    ],
                    [],
                )
            ]
        )
        with pytest.raises(InvalidTokenError):
            verify_access_token_allowed(scheme, token, session)

    def test_verify_access_token_allowed_expired_jti_error(self, mocker):
        scheme = "Bearer"
        token = "abc123"
        exp_at = 199999999

        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(exp_at + 1, timezone.utc),
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == token),
                    ],
                    [AccessToken(id=token, exp=exp_at)],
                )
            ]
        )
        with pytest.raises(ExpiredJTIError):
            verify_access_token_allowed(scheme, token, session)

    def test_verify_access_token_allowed_invalid_token_scheme_error(self, mocker):
        scheme = "SomethingNotBearer"
        token = "abc123"
        exp_at = 199999999

        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(exp_at - 1, timezone.utc),
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == token),
                    ],
                    [AccessToken(id=token, exp=exp_at)],
                )
            ]
        )
        with pytest.raises(InvalidTokenSchemeError):
            verify_access_token_allowed(scheme, token, session)

    def test_verify_access_token_allowed(self, mocker):
        scheme = "Bearer"
        token = "abc123"
        exp_at = 199999999

        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(exp_at - 1, timezone.utc),
        )

        session = UnifiedAlchemyMagicMock(
            data=[
                (
                    [
                        mock.call.query(AccessToken),
                        mock.call.filter(AccessToken.id == token),
                    ],
                    [AccessToken(id=token, exp=exp_at)],
                )
            ]
        )

        verify_access_token_allowed(scheme, token, session)

    def test_validate_access_token_unauthorized(self, mocker):
        token = "abcdef-123"
        now = 19999999

        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(now, timezone.utc),
        )
        mocker.patch(
            "src.api.lib.auth.get_access_token_from_headers",
            return_value=("Bearer", token),
        )
        mocker.patch("src.api.lib.auth.make_response", return_value=flask.Response())
        verify_token_mock = mocker.patch("src.api.lib.auth.verify_access_token_allowed")
        verify_token_mock.side_effect = InvalidTokenError("")

        val = validate_access_token(lambda: prepare_response(200))()
        assert val.status_code == 401, "Expected to get a 401 unauthoritzed!"

    def test_validate_access_token_authorized(self, mocker):
        token = "abcdef-123"
        now = 19999999

        mocker.patch(
            "src.api.lib.auth.get_now_epoch",
            return_value=datetime.fromtimestamp(now, timezone.utc),
        )
        mocker.patch(
            "src.api.lib.auth.get_access_token_from_headers",
            return_value=("Bearer", token),
        )
        mocker.patch("src.api.lib.auth.make_response", return_value=flask.Response())
        mocker.patch("src.api.lib.auth.verify_access_token_allowed", return_value=None)

        mock_request = mocker.MagicMock()
        mock_request.headers = {"Authorization": "Bearer test_token"}
        mocker.patch("src.api.lib.auth.request", mock_request)

        val = validate_access_token(lambda: prepare_response(200))()
        assert val.status_code == 200, "Expected to get a 200 authorized!"
