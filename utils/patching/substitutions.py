"""Find-and-replace patches for the site's text assets (JS, HTML, CSS).

They are applied each time a file is served (utils/assets.py).
"""
from dataclasses import dataclass

from config import LANG


@dataclass(frozen=True)
class Substitution:
    """A simple find-and-replace patch for text assets."""

    old: bytes
    new: bytes


# point the SWF embed at the local language host instead of window.location
_SWF_EMBED_PATCHES = Substitution(
        b"lang:window.location",
        f"lang:'http://{LANG}.pokemon-gl.com/'".encode(),
    )

# patch for Ruffle breaking the volume slider
_VOLUME_SLIDER_PATCHES = Substitution(
        b"return document[movieName];",
        b"return document.getElementById(movieName);",
    )

# file name -> substitutions for just that file
JS_PATCHES: dict[str, tuple[Substitution, ...]] = {
    "pgl.js": (
        # Ruffle only starts a SWF once the browser allows sound, and otherwise shows a play
        # button, which is invisible on the 1x1 music player and covers the volume slider.
        Substitution(
            b"var PGL = function() {\n",
            b"window.RufflePlayer = window.RufflePlayer || {};\n"
            b"window.RufflePlayer.config = $.extend({}, window.RufflePlayer.config, { autoplay: 'on', unmuteOverlay: 'hidden' });\n"
            b"\n"
            b"var PGL = function() {\n",
        ),
        Substitution(
            b"(location.href.match(/\\W(ja|en|fr|it|de|es|ko)\\./) || [null, 'ja'])[1];",
            f"'{LANG}';".encode(),
        ),
        Substitution(
            b"var result = { check: 'https://' + this.getComDomain() + '/pglcheck' };",
            b"return { check: '/pglcheck', form: '/login/pgl.html' };"
        )
    ),
    "register.js": (
        # Enforce that the PGL nickname is the same as the Trainer Club name.
        Substitution(
            b"  $('#header-back-to-top').hide();\n",
            b"  $('#header-back-to-top').hide();\n"
            b"  $('input[name=pgl_name]').val(this.data.username).prop('readonly', true);\n",
        ),
    ),
    "swfembed2.js": (_SWF_EMBED_PATCHES, _VOLUME_SLIDER_PATCHES),
    "swfembed3.js": (_SWF_EMBED_PATCHES, _VOLUME_SLIDER_PATCHES),
    "top.js": (
        # Browsers only allow sound once the visitor has interacted with the page, so if that
        # hasn't happened yet, the front page music starts on their first click or key press.
        Substitution(
            b"    $('<div id=\"sound\"></div>').appendTo(document.body);\n"
            b"    swfobject.embedSWF('/top/assets/swf/sound.swf', 'sound', '1', '1', '9.0.0');\n",
            b"    var startMusic = function () {\n"
            b"      $(document).off('mousedown keydown touchend', startMusic);\n"
            b"      $('<div id=\"sound\"></div>').appendTo(document.body);\n"
            b"      swfobject.embedSWF('/top/assets/swf/sound.swf', 'sound', '1', '1', '9.0.0');\n"
            b"    };\n"
            b"    var soundCheck = new AudioContext();\n"
            b"    if (soundCheck.state === 'running') {\n"
            b"      startMusic();\n"
            b"    } else {\n"
            b"      $(document).on('mousedown keydown touchend', startMusic);\n"
            b"    }\n"
            b"    soundCheck.close();\n",
        ),
        # use Intl.DateTimeFormat so the time respects DST
        Substitution(
            b"d.setTime(d.getTime() + area.tz.offset * 60 * 60 * 1000);\r\n"
            b"        $('#report-records .area .tzname').text(area.tz.name);\r\n"
            b"        $('#report-records .area .time').text(PGL.Utils.zerofill(d.getUTCHours(), 2) + ':' + PGL.Utils.zerofill(d.getUTCMinutes(), 2));",

            b"var _tz_adj = new Intl.DateTimeFormat('en-GB', { timeZone: area.tz.name, hour: '2-digit', minute: '2-digit', hour12: false }).formatToParts(new Date());\r\n"
            b"        $('#report-records .area .tzname').text(area.tz.name);\r\n"
            b"        $('#report-records .area .time').text(_tz_adj.find(function(p){return p.type==='hour';}).value + ':' + _tz_adj.find(function(p){return p.type==='minute';}).value);",
        ),
        Substitution(
            b"checkUrl = $.makeArray(checkUrl);",
            b"return $.Deferred().resolve().promise();"
        ),
        # show the Last Tucked-in Time in the player's time zone
        Substitution(
            b"$('#login-control .member-info-pdw-slepttime').text(data.member.last_up_time);",
            b"$('#login-control .member-info-pdw-slepttime').text(data.member.last_up_time_strict ? "
            b"PGL.Utils.formatTime(Date.parse(data.member.last_up_time_strict.replace(' ', 'T') + '+09:00') / 1000, "
            b"{ format:'SHORT' }) : data.member.last_up_time);",
        ),
    ),
    "profile.js": (
        # show the Last Tucked-in Time in the player's time zone
        Substitution(
            b"$('#soft-synctime .value').text(this.data.member.last_up_time);",
            b"$('#soft-synctime .value').text(this.data.member.last_up_time_strict ? "
            b"PGL.Utils.formatTime(Date.parse(this.data.member.last_up_time_strict.replace(' ', 'T') + '+09:00') / 1000, "
            b"{ format:'SHORT' }) : this.data.member.last_up_time);",
        ),
    ),
}

# substitutions applied to every patchable file
_GLOBAL_SUBS: tuple[Substitution, ...] = (
    Substitution(b"http://cdn2.pokemon-gl.com", b""),
    Substitution(f"http://gus.pokemon.com/{LANG}".encode(), f"/pgl-363/{LANG}".encode()),
    Substitution(b"https://assets.pokemon.com", b"/assets.pokemon.com"),
    Substitution(b"https://www.pokemon.com", b"/www.pokemon.com"),
    Substitution(f"https://edgecastcdn.net/002759/origin/gus.pokemon/{LANG}/".encode(), f"/pgl-363/{LANG}/".encode()),
    Substitution(b"src:gus_src", f"src:'/pgl-363/{LANG}'".encode()),
    Substitution(b"en.pokemon-gl.com", f"{LANG}.pokemon-gl.com".encode()),
    Substitution(b'oncontextmenu="return false"', b""),
    Substitution(b'ondragstart="return false"',   b""),
    Substitution(b'onselectstart="return false"', b""),
)


def apply_substitutions(data: bytes, filename: str) -> bytes:
    """Apply global substitutions, then file-specific ones."""
    for sub in (*_GLOBAL_SUBS, *JS_PATCHES.get(filename, ())):
        data = data.replace(sub.old, sub.new)
    return data
