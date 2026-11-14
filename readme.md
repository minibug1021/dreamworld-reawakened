# Pokemon Dream World - Reawakened

## Tutorial

Both servers are run with [uv](https://docs.astral.sh/uv/), which also downloads a suitable version of Python if you don't have one.

### Windows

- Press the Windows key, type "PowerShell", and open a PowerShell window. Run the command `winget install --id astral-sh.uv -e` to install uv
- If you are on Windows 10, install the git command from the official download [here](https://github.com/git-for-windows/git/releases/download/v2.54.0.windows.1/Git-2.54.0-64-bit.exe)
- If you are on Windows 11, run the command `winget install --id Git.Git -e --source winget` in the PowerShell window
- Close the PowerShell window, so the next one can find the commands you just installed
- Navigate to the folder you want to install the server to
- Hold down shift and right-click in the folder (the empty space, not on a file/folder) and select "open PowerShell window here"
- Run the command `git clone --recursive https://github.com/minibug1021/dreamworld-reawakened.git`
- Navigate into the `dreamworld-reawakened` folder, open a PowerShell window there, and run the command `uv sync`. This installs everything both servers need.

For the Game Sync server (for connecting your DS to the Dream World server, must be done first):
- In a PowerShell window in the `dreamworld-reawakened` folder, run `uv run game_sync_server/server.py` to start the server
- The server will give you a DNS, which you can change from the "Nintendo WFC Settings" menu located on the save file select screen of the Gen5 game.
- Connect to the Game Sync in-game and tuck in a Pokémon.

For the Dream World server (the Pokémon Global Link site):
- Open a second PowerShell window in the `dreamworld-reawakened` folder
- Run `uv run main.py` to start the server. It always runs on port 8080.

### Linux

- Install uv with `curl -LsSf https://astral.sh/uv/install.sh | sh`.
- Install git with your distribution's package manager
- Run `git clone --recursive https://github.com/minibug1021/dreamworld-reawakened.git`, then `cd dreamworld-reawakened` and `uv sync`
- The Game Sync server must be run as root, because the ports it uses (53 and 443) are privileged. Start it with `sudo .venv/bin/python game_sync_server/server.py` from the `dreamworld-reawakened` folder.
- Start the Dream World server as your normal user with `uv run main.py`

## Flash browser setup
Install the [Ruffle browser extension](https://ruffle.rs/), which will allow the Dream World to run on modern browsers such as Firefox and Chrome.

Be mindful that Ruffle is not perfect and will still have issues. Please report new issues as they come up so we can pass them on to the Ruffle team for further investigation.


### Windows

- Install [Basilisk](https://www.basilisk-browser.org/), a browser which still supports NPAPI based plugins.

- Download and install the archived version of [Flash Player 32.0.0.371](https://web.archive.org/web/20200609220527/https://fpdownload.macromedia.com/pub/flashplayer/installers/archive/fp_32.0.0.371_archive.zip) for Windows.

- Navigate to http://127.0.0.1:8080/ in Basilisk.

### Linux

- Install and extract [Basilisk](https://www.basilisk-browser.org/), a browser which still supports NPAPI based plugins.

- Download the archived version of [Flash Player 32.0.0.371](https://web.archive.org/web/20200530062840if_/https://fpdownload.adobe.com/get/flashplayer/pdc/32.0.0.371/flash_player_npapi_linux.x86_64.tar.gz) for Linux.

- Place `libflashplayer.so` into `/usr/lib64/mozilla/plugins`. You may have to create this directory.

- Place the contents of the `usr` folder into `/usr/`.

- Run Basilisk with proper environment variable like so: `MOZ_PLUGIN_PATH=/usr/lib64/mozilla/plugins ./basilisk`

- Navigate to http://127.0.0.1:8080/ in Basilisk.

## Standalone startup
- Load http://127.0.0.1:8080/DreamWorld_data/src/swf/theme/assets/common/main.swf with the standalone Adobe Flash Player (download: [Windows](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_win_sa.exe), [Mac](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_mac_sa.dmg), [Linux](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_linux_sa.x86_64.tar.gz))

# Things that are not working

- Making a wish at the Tree of Dreams
- Sending back Pokémon through the Entralink
- Share Shelf