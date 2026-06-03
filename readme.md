# Pokemon Dream World - Reawakened

In the terminal, after installing Python, run `pip install -r requirements.txt`.

After this, run `python main.py` to start the server.

## Standalone startup
- Load http://127.0.0.1:8080/DreamWorld_data/src/swf/theme/assets/common/main.swf with the standalone Adobe Flash Player (download: [Windows](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_win_sa.exe), [Mac](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_mac_sa.dmg), [Linux](https://archive.org/download/standaloneflashplayers/fp/fp_32/32.0.0.465/flashplayer32_0r0_465_linux_sa.x86_64.tar.gz))

## Flash browser startup

**Ruffle will not work.**
Ruffle currently cannot emulate the Dream World correctly.

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

# Save data manager
This requires the installation of PyQt5 with `pip install PyQt5`

If you open the terminal inside `save_data_manager` and run `python3 save_manager.py`, through a UI you can load a Gen5 save file (.sav only) and "send" a Pokémon to the Dream World. This will modify both `save_data/player_data.json` and `save_data/sleeping_pokemon.json`.

# Other Info

Save data that is currently managed by the server:
- Functionality related to Berries. Planting, watering, and harvesting work as expected. Berries will grow over time and their water level will deplete. When harvesting Berries, they will be placed in the player's Treasure Chest, which will be updated on disk as well.

