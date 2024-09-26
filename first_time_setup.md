## First time setup
- This assumes you're using VSCode on either a Windows or Linux machine. Macs will generally follow the Linux instructions but you'll need to make some tweaks as appropriate (M1's particularly)

### Windows
Note: This is just a suggestion for first time setup on windows. Feel free to ignore if you know what you're doing.

1. Install WSL2
  - https://learn.microsoft.com/en-us/windows/wsl/install
  - Powershell: `wsl --install`
2. Install your favorite Linux distro (Ubuntu is a decent default)
  - Powershell: `wsl --install Ubuntu`
3. Install VSCode
  - https://code.visualstudio.com/
4. Install WSL Extension
  - https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl
5. Open up a new VSCode window and activate a WSL environment
  - Command Palette: `>WSL: Connect to WSL using Distro`
  - Select Ubuntu or whatever you previously installed
6. Clone this (and YakumoDash's) Repository
  - Command Palette: `>Git: clone`

You should be ready to follow the "Linux" instructions now


### Linux
These are the actual platform-agnostic setup instructions

#### Prerequisite software
##### `Python`
- At least 3.8+
- Eg, `sudo apt install python`
- If on WSL, you may also need `sudo apt install python-is-python3`
##### `Make`
- Eg, `sudo apt install make`
##### `docker`
1. Install docker
```
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```
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

#### Prerequisite Git Setup
You'll need to set up credentials with git to clone the secrets submodule.

1. Create an ssh key if one doesn't exist already
  - https://www.digitalocean.com/community/tutorials/how-to-create-ssh-keys-with-openssh-on-macos-or-linux
2. Add your public key to your Github account's settings page
  - `echo ~/.ssh/id_rsa.pub`
  - Using the output of above, follow https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account#adding-a-new-ssh-key-to-your-account
3. Init and update submodules
  - `git submodule update --init`


#### Building Images
- `make build`

Everything should "Just Build"

#### Running YC Backend
- **FIRST TIME ONLY**: `./scripts/first_time_setup.sh`
- `make up_web`

#### Accessing Filebrowser
- http://filebrowser.localhost
- Login by default is `admin:admin`
- If you can access this you're done. Now go set up YakumoDash.