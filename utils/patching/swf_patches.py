"""The ActionScript patches for each SWF.

The patch text constants are named after the ActionScript class they change.
"""
from dataclasses import dataclass
from textwrap import dedent

from config import ROOT_DIR


@dataclass(frozen=True)
class Insertion:
    """Replaces lines of a class in a SWF's decompiled ActionScript.

    `old` is the original line(s) to replace, compared without indentation. It must occur
    exactly `count` times (each occurrence is replaced). With block=True, `old` is the
    header of a brace block (a function, an if/else chain, a switch) and the whole block
    is replaced. The replacement is indented like the first replaced line.
    """

    class_path: str
    old: str
    replacement: str
    block: bool = False
    count: int = 1


# ---------------
# SWF patch content
# ---------------


_PokemonBridge_patch = dedent("""\
    PDW_API = "../api/";
    PDW_API_SSL = "../api/";

    Logger.log("PATH : " + PokemonBridge.PATH);
    Logger.log("API : " + PDW_API);
""")

# the original code checks to see if we are connecting from localhost and tries to load
# it from a different path if we are
_Garden_patch = "this._exteriorLoader.load(new URLRequest(path + \"../../theme/assets/global/parts/interior/\" + islandId + \".swf\" + cacheBuster + version));"

# not actually sure if this is needed but its pretty much the same as the above
_PDW_patch_2 = "PDWBridge.isLocal = false;"

# ffdec decompiles this part of the code incorrectly and leaves behind an empty switch
# statement we have to remove
_closeMoveAlert_fix = ""

# ---------------
# Ruffle compatibility patches
# ---------------

# according to Blupee:
# Ruffle probably needs to assign a default value to root.transform.perspectiveProjection in order to fix this properly
_PDW_patch = dedent("""\
    if(!root.transform.perspectiveProjection)
    {
        root.transform.perspectiveProjection = new flash.geom.PerspectiveProjection();
    }
    root.transform.perspectiveProjection.projectionCenter = new Point(int(stage.stageWidth / 2),int(stage.stageHeight / 2));
""")

_Alert_patch = dedent("""\
    if(!this.root.transform.perspectiveProjection)
    {
        this.root.transform.perspectiveProjection = new flash.geom.PerspectiveProjection();
    }
    this.root.transform.perspectiveProjection.projectionCenter = new Point(int(1003 / 2),int(528 / 2));
""")

# jp.feb19.utils.Tracer calls a shitton of text rendering functions that are really
# expensive in Ruffle and cause the game to freeze for several seconds during init.
# Its an invisible debug panel, so we can just gate that code against its visibility.
_Tracer_update_patch = dedent("""\
    if(!_isShow)
    {
        return;
    }
    tracermc.tf.text = "";
""")

# ---------------
# Feature tweaks
# ---------------

# Shiny art is stored as frame 2 of each species/form SWF, so showing a shiny Pokemon
# only requires selecting frame 2 once its SWF has loaded.

# The renderer keeps the shiny flag of the latest load so the completion handler can
# select frame 2.
_PokemonRenderer_fields_patch = dedent("""\
    private var _placeName:String;

    private var _shiny:Boolean = false;""")

# When a function has a local named `number`, ffdec recompiles the filter
# `.(@number == number)` as `.(number == number)`, which matches every Pokemon. Renaming
# the local in every load function keeps the filter intact.
_PokemonRenderer_number_decl_patch = "var dexNumber:int = param1;"
_PokemonRenderer_number_filter_patch = "this.param = pokemonParams.pokemons.pokemon.(@number == dexNumber)[form];"
_PokemonRenderer_number_error_patch = \
    'throw new ArgumentError("図鑑番号" + dexNumber + ", フォルム番号" + form + "は定義されていません");'
_PokemonRenderer_packageName_patch = dedent("""\
    this._shiny = shiny;
    this.packageName = this.getPackageName(dexNumber,form);""")
_PokemonRenderer_loadToPGLIntro_packageName_patch = "this.packageName = this.getPackageName(dexNumber,form + 100);"

_PokemonRenderer_load_signature_patch = \
    "public function load(param1:int, param2:int, param3:Number = 1, shiny:Boolean = false) : void"
_PokemonRenderer_loadToArea_signature_patch = \
    "public function loadToArea(param1:int, param2:int, param3:Number, param4:Number, param5:Boolean = true, " \
    "shiny:Boolean = false) : void"
_PokemonRenderer_loadToScene_signature_patch = \
    "public function loadToScene(param1:int, param2:int, param3:String, shiny:Boolean = false) : void"

_PokemonRenderer_imageLoaderCompleteHandler_patch = dedent("""\
    if(this._shiny)
    {
       flash.display.MovieClip(this.imageLoader.content).gotoAndStop(2);
    }
    this.imageLoader.alpha = 0;""")

_IPokemonRenderer_load_patch = "function load(param1:int, param2:int, param3:Number = 1, shiny:Boolean = false) : void;"
_IPokemonRenderer_loadToArea_patch = "function loadToArea(param1:int, param2:int, param3:Number, param4:Number, param5:Boolean = true, shiny:Boolean = false) : void;"
_IPokemonRenderer_loadToScene_patch = "function loadToScene(param1:int, param2:int, param3:String, shiny:Boolean = false) : void;"

# render the player's Dream World Pokemon shiny if PDWHomeData says so (Arc and Garden
# make the same call)
_myPokemon_load_patch = "pokemon.load(PDWHomeData.myPokemonNo,PDWHomeData.myPokemonFormNo,0.55,PDWHomeData.myPokemonShiny);"

# the Garden's FarmData and the Share Shelf's ShareData manage the Pokémon the same way
_pokemonShiny_field_patch = dedent("""\
    public var pokemonFormID:Number = 0;
    public var pokemonShiny:Boolean = false;""")


_Main_pokemonShiny_patch = dedent("""\
    this.data.pokemonFormID = PDWHomeData.myPokemonFormNo;
    this.data.pokemonShiny = PDWHomeData.myPokemonShiny;""")

_PokemonFiledArea_loadToScene_patch = "this.pokemonObj.loadToScene(this.data.pokemonID,this.data.pokemonFormID,PokemonRendererScene.CROFT,this.data.pokemonShiny);"
_ShareArea_loadToScene_patch = "this.pokemonObj.loadToScene(this.data.pokemonID,this.data.pokemonFormID,PokemonRendererScene.SHARING_SHELF,this.data.pokemonShiny);"


_RCData_myPokemonShiny_field_patch = dedent("""\
    public var myPokemonFormID:Number = 0;
    public var myPokemonShiny:Boolean = false;""")

_RCData_friendPokemonShiny_field_patch = dedent("""\
    public var friendPokemonFormID:Number = 8;
    public var friendPokemonShiny:Boolean = false;""")

_Room_Main_myPokemonShiny_patch = dedent("""\
    this.rcData.myPokemonFormID = PDWHomeData.myPokemonFormNo;
    this.rcData.myPokemonShiny = PDWHomeData.myPokemonShiny;""")

_Room_Main_friendPokemonShiny_patch = dedent("""\
    this.rcData.friendPokemonFormID = PDWHomeData.anotherPokemonFormNo;
    this.rcData.friendPokemonShiny = PDWHomeData.anotherPokemonShiny;""")

_PokemonArea_myPokemon_loadToScene_patch = "this.myPokemonObj.loadToScene(this.rcData.myPokemonID,this.rcData.myPokemonFormID,PokemonRendererScene.ROOM,this.rcData.myPokemonShiny);"
_PokemonArea_friendPokemon_loadToScene_patch = "this.friendPokemonObj.loadToScene(this.rcData.friendPokemonID,this.rcData.friendPokemonFormID,PokemonRendererScene.ROOM,this.rcData.friendPokemonShiny);"

_DialogPokemonList_patch = "pokemon.loadToArea(data.pokemon_list[i].pokemon_no,data.pokemon_list[i].form_no,82,82,data.pokemon_list[i].shiny);"

_InitPDWHomeData_myPokemon_patch = dedent("""\
    PDWHomeData.myPokemonBall = json.pokemon.ball_name;
    PDWHomeData.myPokemonShiny = Boolean(json.pokemon.shiny);""")

_InitPDWHomeData_myPokemon_reset_patch = dedent("""\
    PDWHomeData.myPokemonBall = "";
    PDWHomeData.myPokemonShiny = false;""")

# The Dream Pal map counts the islands to draw before it takes the island the player came
# from out of the list, so with 4 or fewer islands it reads past the end of the list.
_World_moveCount_patch = dedent("""\
    json.friend_list.splice(i,1);
    max = Math.min(4,json.friend_list.length);
    break;""")

# Ruffle: keep main.swf's copy of the defaultVolume SharedObject up to date.
_SoundController_sendVolume_patch = dedent("""\
    ExternalInterface.addCallback("sendVolume",function(param1:*):void
    {
       my_so.data.defaultVolume = param1;
       receivedFromJavaScript(param1);
    });""")

# ---------------
# SWF paths / insertions
# ---------------

_SWF_DIR = ROOT_DIR / "dreamworld_assets" / "shared.pokemon-gl.com" / "src" / "swf"

SWF_PATHS = {
    "main.swf":       _SWF_DIR / "theme" / "assets" / "common" / "main.swf",
    "pdw_home.swf":   _SWF_DIR / "pdw" / "assets" / "pdw_home.swf",
    "pdw.swf":        _SWF_DIR / "pdw" / "assets" / "pdw.swf",
    "pdw_garden.swf": _SWF_DIR / "pdw" / "assets" / "pdw_garden.swf",
    "poke.swf":       _SWF_DIR / "theme" / "assets" / "common" / "poke.swf",
    "pdw_arc.swf":    _SWF_DIR / "pdw" / "assets" / "pdw_arc.swf",
    "pdw_farm.swf":   _SWF_DIR / "pdw" / "assets" / "pdw_farm.swf",
    "pdw_room.swf":   _SWF_DIR / "pdw" / "assets" / "pdw_room.swf",
    "pdw_share.swf":  _SWF_DIR / "pdw" / "assets" / "pdw_share.swf",
    "pdw_world.swf":  _SWF_DIR / "pdw" / "assets" / "pdw_world.swf",
}

def _pokemon_renderer_patches(package: str) -> tuple[Insertion, ...]:
    """poke.swf has the renderer twice, in com.pokemon_gl.pdw and com.pokemon_gl.pdw2."""
    renderer = f"com.pokemon_gl.{package}.display.PokemonRenderer"
    interface = f"com.pokemon_gl.{package}.display.IPokemonRenderer"
    return (
        Insertion(renderer, "this.imageLoader.alpha = 0;", _PokemonRenderer_imageLoaderCompleteHandler_patch),
        Insertion(renderer, "var number:int = param1;", _PokemonRenderer_number_decl_patch, count=4),
        Insertion(renderer, "this.param = pokemonParams.pokemons.pokemon.(@number == number)[form];",
                  _PokemonRenderer_number_filter_patch, count=4),
        Insertion(renderer, 'throw new ArgumentError("図鑑番号" + number + ", フォルム番号" + form + "は定義されていません");',
                  _PokemonRenderer_number_error_patch, count=4),
        Insertion(renderer, "this.packageName = this.getPackageName(number,form);",
                  _PokemonRenderer_packageName_patch, count=3),
        Insertion(renderer, "this.packageName = this.getPackageName(number,form + 100);",
                  _PokemonRenderer_loadToPGLIntro_packageName_patch),
        Insertion(renderer, "public function loadToScene(param1:int, param2:int, param3:String) : void",
                  _PokemonRenderer_loadToScene_signature_patch),
        Insertion(renderer, "public function loadToArea(param1:int, param2:int, param3:Number, param4:Number, "
                            "param5:Boolean = true) : void",
                  _PokemonRenderer_loadToArea_signature_patch),
        Insertion(renderer, "public function load(param1:int, param2:int, param3:Number = 1) : void",
                  _PokemonRenderer_load_signature_patch),
        Insertion(renderer, "private var _placeName:String;", _PokemonRenderer_fields_patch),
        Insertion(interface, "function loadToScene(param1:int, param2:int, param3:String) : void;",
                  _IPokemonRenderer_loadToScene_patch),
        Insertion(interface, "function loadToArea(param1:int, param2:int, param3:Number, param4:Number, "
                             "param5:Boolean = true) : void;",
                  _IPokemonRenderer_loadToArea_patch),
        Insertion(interface, "function load(param1:int, param2:int, param3:Number = 1) : void;",
                  _IPokemonRenderer_load_patch),
    )


INSERTIONS: dict[str, tuple[Insertion, ...]] = {
    "main.swf": (
        Insertion("bfp.common.PokemonBridge",
                  'Logger.log("PATH : " + PokemonBridge.PATH);\nLogger.log("API : " + PDW_API);',
                  _PokemonBridge_patch),
        Insertion("bfp.main.SoundController", 'ExternalInterface.addCallback("sendVolume",this.receivedFromJavaScript);',
                  _SoundController_sendVolume_patch),
    ),
    "pdw_home.swf": (
        # InitPDWHomeData copies the API response into PDWHomeData, so the shiny flag needs
        # the same copy. Every SWF shares pdw.swf's PDWHomeData, which pdw.swf loads first,
        # and that copy has no shiny field. AVM2 class objects are dynamic, so setting
        # myPokemonShiny here creates it, and the SWFs that read it see the same value.
        Insertion("bfp.tpc.pdw.home.InitPDWHomeData", 'PDWHomeData.myPokemonBall = "";',
                  _InitPDWHomeData_myPokemon_reset_patch),
        Insertion("bfp.tpc.pdw.home.InitPDWHomeData", "PDWHomeData.myPokemonBall = json.pokemon.ball_name;",
                  _InitPDWHomeData_myPokemon_patch),
    ),
    "pdw.swf": (
        Insertion("bfp.tpc.pdw.pdw.PDW",
                  "root.transform.perspectiveProjection.projectionCenter = "
                  "new Point(int(stage.stageWidth / 2),int(stage.stageHeight / 2));", _PDW_patch),
        Insertion("bfp.tpc.pdw.pdw.PDW", 'PDWBridge.isLocal = localConnection.domain == "localhost";', _PDW_patch_2),
        Insertion("bfp.tpc.pdw.dialog.Alert",
                  "this.root.transform.perspectiveProjection.projectionCenter = new Point(int(1003 / 2),int(528 / 2));",
                  _Alert_patch),
        Insertion("bfp.tpc.pdw.pdw.PDW", "switch(0)", _closeMoveAlert_fix, block=True),
        Insertion("bfp.tpc.pdw.dialog.DialogPokemonList",
                  "pokemon.loadToArea(data.pokemon_list[i].pokemon_no,data.pokemon_list[i].form_no,82,82);",
                  _DialogPokemonList_patch),
        Insertion("jp.feb19.utils.Tracer", 'tracermc.tf.text = "";', _Tracer_update_patch),
    ),
    "pdw_garden.swf": (
        Insertion("bfp.tpc.pdw.garden.Garden",
                  "pokemon.load(PDWHomeData.myPokemonNo,PDWHomeData.myPokemonFormNo,0.55);",
                  _myPokemon_load_patch),
        Insertion("bfp.tpc.pdw.garden.Garden", 'if(new LocalConnection().domain == "localhost")',
                  _Garden_patch, block=True),
    ),
    "poke.swf": _pokemon_renderer_patches("pdw") + _pokemon_renderer_patches("pdw2"),
    "pdw_arc.swf": (
        Insertion("bfp.tpc.pdw.arc.Arc", "pokemon.load(PDWHomeData.myPokemonNo,PDWHomeData.myPokemonFormNo,0.55);",
                  _myPokemon_load_patch),
    ),
    "pdw_farm.swf": (
        Insertion("bfp.pdw.farm.objects.PokemonFiledArea",
                  "this.pokemonObj.loadToScene(this.data.pokemonID,this.data.pokemonFormID,"
                  "PokemonRendererScene.CROFT);", _PokemonFiledArea_loadToScene_patch),
        Insertion("bfp.pdw.farm.document.Main", "this.data.pokemonFormID = PDWHomeData.myPokemonFormNo;",
                  _Main_pokemonShiny_patch),
        Insertion("bfp.pdw.farm.FarmData", "public var pokemonFormID:Number = 0;", _pokemonShiny_field_patch),
    ),
    "pdw_share.swf": (
        Insertion("bfp.pdw.share.view.PokemonArea",
                  "this.pokemonObj.loadToScene(this.data.pokemonID,this.data.pokemonFormID,"
                  "PokemonRendererScene.SHARING_SHELF);", _ShareArea_loadToScene_patch),
        Insertion("bfp.pdw.share.document.Main", "this.data.pokemonFormID = PDWHomeData.myPokemonFormNo;",
                  _Main_pokemonShiny_patch),
        Insertion("bfp.pdw.share.ShareData", "public var pokemonFormID:Number = 0;", _pokemonShiny_field_patch),
    ),
    "pdw_room.swf": (
        Insertion("bfp.pdw.room.objects.PokemonArea",
                  "this.myPokemonObj.loadToScene(this.rcData.myPokemonID,this.rcData.myPokemonFormID,"
                  "PokemonRendererScene.ROOM);", _PokemonArea_myPokemon_loadToScene_patch, count=2),
        Insertion("bfp.pdw.room.objects.PokemonArea",
                  "this.friendPokemonObj.loadToScene(this.rcData.friendPokemonID,this.rcData.friendPokemonFormID,"
                  "PokemonRendererScene.ROOM);", _PokemonArea_friendPokemon_loadToScene_patch),
        Insertion("bfp.pdw.room.document.Main", "this.rcData.friendPokemonFormID = PDWHomeData.anotherPokemonFormNo;",
                  _Room_Main_friendPokemonShiny_patch),
        Insertion("bfp.pdw.room.document.Main", "this.rcData.myPokemonFormID = PDWHomeData.myPokemonFormNo;",
                  _Room_Main_myPokemonShiny_patch),
        Insertion("bfp.pdw.common_y.RCData", "public var friendPokemonFormID:Number = 8;",
                  _RCData_friendPokemonShiny_field_patch),
        Insertion("bfp.pdw.common_y.RCData", "public var myPokemonFormID:Number = 0;",
                  _RCData_myPokemonShiny_field_patch),
    ),
    "pdw_world.swf": (
        Insertion("bfp.tpc.pdw.world.World", "json.friend_list.splice(i,1);\nbreak;", _World_moveCount_patch),
    ),
}

# SWFs whose main timeline is cut to its first frame (see timeline.py)
FIRST_FRAME_ONLY = {"pdw_world.swf"}
