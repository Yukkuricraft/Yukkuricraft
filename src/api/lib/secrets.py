from enum import Enum
from pathlib import Path
from base64 import b64encode
from nacl import encoding, public  # type: ignore


class InvalidSecretException(Exception):
    pass


class SecretsOption(Enum):
    GH_TOKEN = 1


class Secrets:
    """
    Eventually a boto3 SM wrapper?
    """

    base_dir = Path("secrets/")

    def __init__(self):
        pass

    def encrypt_secret(self, public_key: str, secret_value: str) -> str:
        """Encrypt a Unicode string using the public key."""
        public_key = public.PublicKey(
            public_key.encode("utf-8"), encoding.Base64Encoder()
        )
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return b64encode(encrypted).decode("utf-8")

    def get_secret(self, secret: SecretsOption):
        if secret == SecretsOption.GH_TOKEN:
            self.get_github_token()
        else:
            raise InvalidSecretException()

    def get_github_token(self):
        secret_location = Path("secrets/gh_token")
        with open(self.base_dir / secret_location) as f:
            return f.read()
