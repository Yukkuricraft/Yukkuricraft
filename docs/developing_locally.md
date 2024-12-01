# Developing Locally
- This assumes you're using VSCode on either a Windows or Linux machine. Macs will generally follow the Linux instructions but you'll need to make some tweaks as appropriate (M1's particularly)

## Windows/WSL
- Follow the one-time [Windows setup instructions](windows_first_time_setup.md) first

## Prerequisite software
### `Python`
- At least 3.8+
- Eg, `sudo apt install python`
- If on WSL, you may also need `sudo apt install python-is-python3`
### `Make`
- Eg, `sudo apt install make`
### `docker`
1. Install docker
    - If on Linux
    ```
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    ```
    - If on Windows/WSL: https://docs.docker.com/desktop/wsl/
2. Add yourself to the `docker` group
```
sudo groupadd docker
sudo usermod -aG docker $USER
```
3. Reload shell
```
su - $USER
```
4. Confirm you can call docker commands
```
docker ps
```
### `MySQL`
Note: This is only necessary if you're `pip install -r requirements.txt`'ing in your workspace. This is not necessary if you are only building the container images.
1. If on linux including WSL, `sudo apt-get install libmysqlclient-dev`
  - This is only necessary if you're seeing an error similar to `mysql_config not found` when installing requirements with pip

### Prerequisite Git Setup
You'll need to set up credentials with git to clone the secrets submodule.

1. Create an ssh key if one doesn't exist already
    - https://www.digitalocean.com/community/tutorials/how-to-create-ssh-keys-with-openssh-on-macos-or-linux
    - Eg, `ssh-keygen`
2. Add your public key to your Github account's settings page
    - `echo ~/.ssh/id_rsa.pub`
    - Using the output of above, follow https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account#adding-a-new-ssh-key-to-your-account
3. Init and update submodules
    - `git submodule update --init`


### Building Images
- `make build`

Everything should "Just Build"

### Running YC Backend
- **FIRST TIME ONLY**: `./scripts/first_time_setup.sh`
- `make up_web`
- Backend containers should now be up and running.

### Accessing Filebrowser
- http://filebrowser.localhost
- Login by default is `admin:admin`
- If you can access the link above you're done. Now go set up [YakumoDash](https://github.com/Yukkuricraft/YakumoDash).