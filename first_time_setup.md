## First time setup

Disclaimer: This is gross and needs an overhaul.



1. Requires [pyenv](https://github.com/pyenv/pyenv#installation)
2. `pyenv install 3.10.5`
3. If configured correctly, running `python --version` inside this repo should return `Python 3.10.5`
4. `pip install -r requirements.txt`
  - Installing the `mysqlclient` library may fail if `mysql` is not installed locally on the host system.
5. `make up_web`
6. Clone `YakumoDash` and run `make up_node` inside there.
7. Probably stuff I'm forgetting :-/