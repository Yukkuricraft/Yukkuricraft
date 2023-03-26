import requests


from typing import Dict

from src.common.logger_setup import logger
from src.api.lib.secrets import Secrets, SecretsOption

class InvalidRepositoryException(Exception):
  pass

class SecretUpdateFailedException(Exception):
  pass

class Github:
  repo_owner: str = "Yukkuricraft"
  base_url: str = "https://api.github.com"

  common_headers: Dict[str, str]
  secrets: Secrets

  def __init__(self):
    self.secrets = Secrets()

    self.common_headers = {
      "accept": "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28",
      "Authorization": f"Bearer {self.secrets.get_secret(SecretsOption.GH_TOKEN)}",
    }

  def check_status_code(self, r: requests.request, ):
    if r.status_code != 200:
      logger.warning("Failed to get repository public key")
      logger.warning(r.body)
      raise InvalidRepositoryException()

  def get_repository_public_key(self, repository: str):
    path = f"/repos/{self.repo_owner}/{repository}/actions/secrets/public-key"

    r = requests.get(self.base_url + path, headers=self.common_headers)
    self.check_status_code(r)
    return r.json()

  def get_repository_secret(self, repository: str, secret_name: str):
    path = f"/repos/{self.repo_owner}/{repository}/actions/secrets/{secret_name}"

    r = requests.get(self.base_url + path, headers=self.common_headers)
    self.check_status_code(r)
    return r.json()

  def update_repository_secret(self, repository: str, secret_name: str, secret_value: str):
    path = f"/repos/{self.repo_owner}/{repository}/actions/secrets/{secret_name}"

    repo_pubkey = self.get_repository_public_key(repository)

    data = {
      "encrypted_value": self.secrets.encrypt_secret(repo_pubkey["key"], secret_value),
      "key_id": repo_pubkey["key_id"],
    }

    r = requests.put(self.base_url + path, headers = self.common_headers, data=data)
    if r.status_code != 201:
      raise SecretUpdateFailedException()