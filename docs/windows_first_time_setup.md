# Windows First Time Setup
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

You should be ready to follow the [rest of the instructions now](developing_locally.md)

