"""Find-and-replace patches for the site's text assets (JS, HTML, CSS).

They are applied each time a file is served (utils/assets.py).
"""
from dataclasses import dataclass
from functools import cache

from config import SUPPORTED_LANGUAGES
from utils.language import current_language


@dataclass(frozen=True)
class Substitution:
    """A simple find-and-replace patch for text assets."""

    old: bytes
    new: bytes


def _swf_embed_patch(lang: str) -> Substitution:
    """Point the SWF embed at the language's host instead of window.location."""
    return Substitution(b"lang:window.location", f"lang:'http://{lang}.pokemon-gl.com/'".encode())


# patch for Ruffle breaking the volume slider
_VOLUME_SLIDER_PATCHES = Substitution(
        b"return document[movieName];",
        b"return document.getElementById(movieName);",
    )


@cache
def _file_subs(lang: str) -> dict[str, tuple[Substitution, ...]]:
    """File name -> substitutions for that file, for a site language."""
    return {
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
                f"'{lang}';".encode(),
            ),
            # The language links go to /language/<lang>.
            Substitution(
                b"    $('#select-language a').each(function () {\n"
                b"      var lang = $(this).attr('href').match(/(\\w\\w)\\./)[1];\n"
                b'      $(this).click(function () {\n'
                b"        var cookie = 'selected-language=' + lang + ';';\n"
                b"        cookie += 'path=/;'\n"
                b"        var domain = location.hostname.replace(/^[-\\w]+\\.([-\\w]+\\.[-\\w]+)$/, '$1');\n"
                b'        if (domain != location.hostname) {\n'
                b"          cookie += 'domain=' + domain + ';';\n"
                b'        }\n'
                b'        var expires = new Date(); expires.setTime(expires.getTime() + 365 * 24 * 60 * 60 * 1000);\n'
                b"        cookie += 'expires=' + expires.toGMTString() + ';';\n"
                b'        document.cookie = cookie;\n'
                b"      }).attr({ href:'http://' + location.hostname.replace(/\\w\\w\\./, lang + '.') });\n"
                b'    });\n',
                b"    // the language links are handled by the server (/language/<lang>)\n"
            ),
            Substitution(
                b"var result = { check: 'https://' + this.getComDomain() + '/pglcheck' };",
                b"return { check: '/pglcheck', form: '/login/pgl.html' };"
            )
        ),
        "register.js": (
            Substitution(
                b"var src = '../../src/swf/top/assets/' + PGL.language + '/images/rom-image-'",
                b"var src = '/src/swf/top/' + PGL.language + '/images/rom-image-'"
            ),
            # Enforce that the PGL nickname is the same as the Trainer Club name.
            Substitution(
                b"  $('#header-back-to-top').hide();\n",
                b"  $('#header-back-to-top').hide();\n"
                b"  $('input[name=pgl_name]').val(this.data.username).prop('readonly', true);\n",
            ),
        ),
        "swfembed2.js": (_swf_embed_patch(lang), _VOLUME_SLIDER_PATCHES),
        "swfembed3.js": (_swf_embed_patch(lang), _VOLUME_SLIDER_PATCHES),
        "top.js": (
            # For now we force JA/KO to use the same login flow as the EU languages.
            Substitution(
                b"      if (PGL.language == 'ja') {\n"
                b"        loginUrl = this.host.getPdcLoginUrl();\n"
                b"      } else if (PGL.language == 'ko') {\n"
                b"        loginUrl = this.host.getPkiLoginUrl();\n"
                b"      } else {\n"
                b"        loginUrl= this.host.getComLoginUrl();\n"
                b"      }\n",
                b"      loginUrl = this.host.getComLoginUrl();\n"
            ),
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
        # Certain levels of Windows scaling has issues where lines break when selected.
        "dialog.css": (
            Substitution(
                b"#dialog-avatar #dialog-avatar-list ul {\n"
                b"  overflow: hidden;\n"
                b"  list-style-type: none;\n"
                b"}",
                b"#dialog-avatar #dialog-avatar-list ul {\n"
                b"  overflow: hidden;\n"
                b"  list-style-type: none;\n"
                b"  display: grid;\n"
                b"  grid-template-columns: repeat(8, auto);\n"
                b"  justify-content: start;\n"
                b"}",
            ),
            Substitution(
                b"#dialog-avatar #dialog-avatar-list li.selected {\n"
                b"  border: 1px solid red;\n"
                b"  padding: 0;\n",
                b"#dialog-avatar #dialog-avatar-list li.selected {\n"
                b"  outline: 1px solid red;\n"
                b"  outline-offset: -1px;\n",
            ),
        ),
        "theme.js": (
            Substitution(
                b"(location.href.match(/\\W(ja|en|fr|it|de|es|ko)\\./) || [null, 'ja'])[1];",
                f"'{lang}';".encode(),
            ),
        ),
        "profile.js": (
            Substitution(
                b"var src = '/top/assets/' + PGL.language + '/images/rom-image-'",
                b"var src = '/src/swf/top/' + PGL.language + '/images/rom-image-'"
            ),
            Substitution(
                b"src:'/top/assets/' + PGL.language + '/images/' + logo",
                b"src:'/src/swf/top/' + PGL.language + '/images/' + logo"
            ),
            # show the Last Tucked-in Time in the player's time zone
            Substitution(
                b"$('#soft-synctime .value').text(this.data.member.last_up_time);",
                b"$('#soft-synctime .value').text(this.data.member.last_up_time_strict ? "
                b"PGL.Utils.formatTime(Date.parse(this.data.member.last_up_time_strict.replace(' ', 'T') + '+09:00') / 1000, "
                b"{ format:'SHORT' }) : this.data.member.last_up_time);",
            ),
        ),
    }

@cache
def _global_subs(lang: str) -> tuple[Substitution, ...]:
    """Substitutions applied to every patchable file, for a site language."""
    return (
        # the language links set the visitor's language (api/server.py), before the
        # en.pokemon-gl.com substitution below can change the English one
        *(Substitution(f'href="http://{link}.pokemon-gl.com"'.encode(), f'href="/language/{link}"'.encode())
          for link in SUPPORTED_LANGUAGES),
        Substitution(b"http://cdn2.pokemon-gl.com", b""),
        Substitution(f"http://gus.pokemon.com/{lang}".encode(), f"/pgl-363/{lang}".encode()),
        Substitution(b"https://assets.pokemon.com", b"/assets.pokemon.com"),
        Substitution(b"https://www.pokemon.com", b"/www.pokemon.com"),
        Substitution(f"https://edgecastcdn.net/002759/origin/gus.pokemon/{lang}/".encode(), f"/pgl-363/{lang}/".encode()),
        Substitution(b"src:gus_src", f"src:'/pgl-363/{lang}'".encode()),
        Substitution(b"en.pokemon-gl.com", f"{lang}.pokemon-gl.com".encode()),
        Substitution(b'oncontextmenu="return false"', b""),
        Substitution(b'ondragstart="return false"',   b""),
        Substitution(b'onselectstart="return false"', b""),
    )


def apply_substitutions(data: bytes, filename: str) -> bytes:
    """Apply global substitutions, then file-specific ones, for the visitor's language."""
    lang = current_language()
    for sub in (*_global_subs(lang), *_file_subs(lang).get(filename, ())):
        data = data.replace(sub.old, sub.new)
    return data
