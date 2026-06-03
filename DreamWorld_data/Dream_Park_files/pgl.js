// ------------------------------------------------------
var PGL = function() {
  var that = this;
  $.when(this.ready()).then($.proxy(this.run, this));
};

PGL.NOT_LOGGED_IN      = 0;
PGL.NOT_SIGNED_UP      = 1;
PGL.TRIAL              = 2;
PGL.INTERIM_REGISTERED = 3;
PGL.REGISTERED         = 4;

PGL.NEWS_COUNT = 10;

PGL.pageStartedAt = new Date().getTime();
PGL.language = (location.href.match(/\W(ja|en|fr|it|de|es|ko)\./) || [null, 'ja'])[1];
PGL.setMain = function(func) { PGL.main = func };

PGL.prototype = {
  run: function() {
    if (PGL.main) $.proxy(PGL.main, this)();
  },
  ready: function() {
    var dfd = $.Deferred();
    var that = this;
    
    this.data = null;
    this.state = null;
    this.level = PGL.NOT_LOGGED_IN;
    var isIOS = navigator.userAgent.match(/iPad|iPhone|iPod/), isAndroid = navigator.userAgent.match(/Android/);
    this.pageHasSound = new RegExp('^/(pdw|campaign|mailer|customize|wifi|report)/').test(location.pathname);
    this.pageHasSound = this.pageHasSound || location.pathname == '/';
    this.pageHasSound = this.pageHasSound && !isIOS && !isAndroid;
    this.pageHasFlash = new RegExp('^/(pdw|campaign|mailer|customize)/').test(location.pathname);
    this.apiNeedPing = new RegExp('^/(pdw|campaign|mailer|customize|wifi|report|profile)/').test(location.pathname);
    this.host = new PGL.Host();
    
    this._initHtml1();
    
    if (this.pageHasFlash && navigator.userAgent.match(/iPad|iPhone|iPod/)) {
      this.showDialog(PGL.Text.get('global.env_not_supported'), { ok: function () { location = '/'; }});
    }
    
    var ping = (location.pathname == '/' || this.apiNeedPing) ? 0 : 1;
    var req = $.get('/api/', { p:'pgl.top.init', ping:ping, now:new Date().getTime() })
    .success(function(data) {
      //console && console.log('pgl.top.init', data);
      $.proxy(that._setState, that)(data);
      
      if (that.level == PGL.NOT_SIGNED_UP && !/^\/(register|support)\//.test(location.pathname)) {
        location = '/register/';
      }
    })
    .error(function(e) {
      //console && console.log('pgl.top.init', 'error', arguments);
      // TODO: handle error
    }).complete(function() {
      $.proxy(that._initHtml2, that)();
      dfd.resolve();
    });

    return dfd.promise();
  },
  _initHtml1: function() {
    $('body').addClass('language-' + PGL.language);
    $('#head-menu a').each(function () {
      if (location.pathname.indexOf($(this).attr('href')) == 0) {
        $(this).parent().addClass('selected');
      }
    });
    $('#select-language a').each(function () {
      var lang = $(this).attr('href').match(/(\w\w)\./)[1];
      $(this).click(function () {
        var cookie = 'selected-language=' + lang + ';';
        cookie += 'path=/;'
        var domain = location.hostname.replace(/^[-\w]+\.([-\w]+\.[-\w]+)$/, '$1');
        if (domain != location.hostname) {
          cookie += 'domain=' + domain + ';';
        }
        var expires = new Date(); expires.setTime(expires.getTime() + 365 * 24 * 60 * 60 * 1000);
        cookie += 'expires=' + expires.toGMTString() + ';';
        document.cookie = cookie;
      }).attr({ href:'http://' + location.hostname.replace(/\w\w\./, lang + '.') });
    });
    if ({ en:1, fr:1, it:1, de:1, es:1 }[PGL.language]) {
      var gus_src = this.host.code == 2918 ? 'http://gus.pokemon.com/' + PGL.language + '/' : 'http://' + this.host.getComDomain() + '/pgl-363/' + PGL.language + '/';
      $('body').css({ 'padding-top':56 }).prepend($('<iframe id="gus" border="0" frameborder="0" allowtransparency="true" scrolling="no" marginwidth="0" marginheight="0"></iframe>').attr({ src:gus_src }));
    }
  },
  _initHtml2: function() {
    $('body').addClass(this.state || 'not-logged-in');
    if (!this.data) return;
    if (this.level >= PGL.TRIAL) {
      $('#header-avatar').append(PGL.Utils.getAvatarImage(this.data.member.avator_id));
      PGL.Utils.packText($('#header-pglname').text(this.data.member.pgl_name));
      PGL.Utils.packText($('#header-romname').text(this.data.member.rom_name));
      var rombutton = $('<a></a>');
      console.log("gsid_count: ", this.data.member.gsid_count);
      if (this.data.member.gsid_count < 1) {
        rombutton
          .attr('href', '/profile/#/register-gsid/')
          .css({'background-position': '0 bottom'});
      } else if (this.data.member.gsid_count <= 1) {
        rombutton
          .attr('href', '/profile/#/register-gsid/')
          .css({'background-position': '-116px bottom'});
      } else if (this.data.member.gsid_count >= 2) {
        rombutton
          .attr('href', '/profile/#/change-rom/')
          .css({'background-position': '-232px bottom'});
      }
      rombutton
        .appendTo($('#header-rom-change'));
      $('#header .logged-in, #right-buttons .logged-in').show();
      
      
      var trafficId = this.data.member.world_id * 12345 - 6789;
      var trafficType = this.level == PGL.TRIAL ? 'trial' : 'product';
      $('#footer .trafficy').attr({ href:'/traffic/' + trafficType + '_' + trafficId + '/' }).show();
    } else {
      
    }
    
    var isIOS = navigator.userAgent.match(/iPad|iPhone|iPod/), isAndroid = navigator.userAgent.match(/Android/);
    if (isIOS || isAndroid) {
      $('<div id="sound-mute"></div>').appendTo(document.body);
      swfobject.embedSWF('/src/swf/assets/global/swf/mute.swf', 'sound-mute', '1', '1', '10.0.0');
    } else if (this.pageHasSound) {
      var flashvars = {};
      flashvars.color1 = flashvars.color2 = 0x000000;
      if (this.level == PGL.NOT_LOGGED_IN) {
        flashvars.color1 = flashvars.color2 = 0xFFFFFF;
      } else if (this.data.member && (this.data.member.rom_id == '21' || this.data.member.rom_id == '23')) {
        flashvars.color1 = flashvars.color2 = 0xFFFFFF;
      }
      if (/^\/?$/.test(location.pathname)) flashvars.color1 = flashvars.color2 = 0xFFFFFF;
      swfobject.embedSWF('http://' + this.host.getSwfHost() + '/src/swf/assets/global/swf/volume.swf', 'header-volume-swf', 56, 20, '10.0.0', null, flashvars, { wmode:'transparent', allowScriptAccess:'always' });
    }
  },
  _setState: function(data) {
    var that = this;
    this.data = data;

    if (!data.member) {
      this.level = PGL.NOT_LOGGED_IN;
    } else if (!data.member.pgl_name) {
      this.level = PGL.NOT_SIGNED_UP;
    } else if (data.member.trial_flag == '1') {
      this.level = PGL.TRIAL;
      this.state = 'trial';
    } else if (data.member.rom_id != '20' && data.member.rom_id != '21' 
        && data.member.rom_id != '22' && data.member.rom_id != '23') {
      this.level = PGL.INTERIM_REGISTERED;
    } else {
      this.level = PGL.REGISTERED;
    }
    if (this.level == PGL.REGISTERED) {
      if (data.member.rom_id == '20') {
        this.state = 'logged-in-white';
      } else if (data.member.rom_id == '21') {
        this.state = 'logged-in-black';
      } else if (data.member.rom_id == '22') {
        this.state = 'logged-in-white2';
      } else if (data.member.rom_id == '23') {
        this.state = 'logged-in-black2';
      }
    } else {
      for (var key in PGL) {
        if (!/^[A-Z_]$/.test(key)) continue;
        if (this.level == PGL[key]) {
          this.state = key.replace(/_/g, '-').toLowerCase();
        }
      }
    }

    if (!this.data.medals || !this.data.medals.length) {
      this.data.medals = [];
    }

  },
  getApi: function(api, param, callback, reloadOnError) {
    return this._callApi('/api/', 'get', api, param, callback, reloadOnError);
  },
  postApi: function(api, param, callback, reload_on_error) {
    return this._callApi('/api/', 'post', api, param, callback, reload_on_error);
  },
  _callApi: function(url, method, api, param, callbacks, reloadOnError) {
    /*
    if (typeof param == 'function') {
      reload_on_error = callback;
      callback = param;
      param = {};
    } else {
      param = param || {};
    }*/
    var that = this;
    var data = this.data;
    if (!$.isArray(callbacks)) callbacks = [callbacks];
    var errorHandler = function(error) {
        that.showDialog(error, { ok: function () { if (reloadOnError) location.reload(); }});
    };
    if (typeof reloadOnError == 'function') errorHandler = reloadOnError;
    if (data.token) param.token = data.token;
    return $.ajax({
      type: method,
      url: url + '?p=' + api, 
      data: param,
      dataType: 'json',
      success: function(data) {
        var error = that._getApiError(data);
        if (error) {
          if (typeof console != 'undefined' && console.log) console.log(api)
          errorHandler(error);
        } else {
          for(var i = 0; i < callbacks.length; i++) {
            (callbacks[i]).apply(that, [data]);
          }
        }
      },
      error: function (xhr, status) {
        if (api == 'pgl.top.init' || api == 'pgl.top.index') {
          return;
        }
        errorHandler(PGL.Text.get('error.load_error'));
      }
    });
  },
  _getApiError: function(result) {
    if (result.error) {
      for (var i in result.error.details || {}) {
        return result.error.details[i];
      }
    }
    return null;
  },
  showDialog: function(text, option) {
    if (text.replace) text = text.replace(/\\n/g, '\n');
    option = option || {};
    var body = $('<div class="dialog-body"></div>');
    $.each(text.split('\n'), function (index, text) {
      var p = $('<p></p>').appendTo(body);
      if (option.auto_link) {
        text = text.replace(/((?:\r|\n|.)*?)(s?https?:\/\/[-_.!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#]*[-_!~*\'()a-zA-Z0-9;\/?:\@&=+\$,%#])/g, function (match, plain, link) {
          p.append($('<span></span>').text(plain), $('<a target="_blank"></a>').attr({ href:link }).text(link));
          return '';
        });
      }
      if (option.html) {
        p.html(text);
      } else {
        var regex = $.map(['black2', 'white2', 'black', 'white'], function (a) { return PGL.Text.get('global.' + a); }).join('|');
        regex = new RegExp('((?:\\r|\\n|.)*?)(' + regex + ')', 'g');
        text = text.replace(regex, function (match, plain, gamecard) {
          p.append($('<span></span>').text(plain), $('<span class="game-card-name"></span>').text(gamecard));
          return '';
        });
        p.append($('<span></span>').text(text));
      }
    });
    
    var buttons = $('<div class="dialog-buttons"></div>').appendTo(body);
    var hasButton = false;
    
    $.each(['ok', 'back', 'wakeup', 'register', 'close'], function (index, type) {
      if (option[type]) {
        hasButton = true;
        $('<a></a>').click(function () {
          $.unblockUI();
          if ($.isFunction(option[type])) {
            (option[type])();
          }
        }).addClass('dialog-buttons-' + type).appendTo(buttons);
      }
    });
    
    var dialog = $('<div class="dialog alert"></div>').append(body).appendTo(document.body).corner('10px');
    $.blockUI({ message:dialog, css:{
        'border-style':'none', background:'transparent', cursor:'default',
        left:'50%', 'margin-left':dialog.width() * -0.5 - 20,
        top:'50%', 'margin-top':dialog.height() * -0.5
      }, overlayCSS: { cursor: 'default' }
    });
    
    if (!hasButton) {
      setTimeout(function () {
        $.unblockUI();
      }, 2200);
    }

  },
  showPopup: function (dialog, callback, css) {
    var dfd = $.Deferred();
    var th = this;
    css = $.extend({ 
      width: '440px', 'border-style': 'none', background: 'transparent', cursor: 'default', 
      top:Math.max(132, $(window).scrollTop() + 50), left: '50%', 'margin-left': dialog.width() * -0.5
    }, css);
    $(document.body).block({ message: dialog, css:css, overlayCSS: { cursor: 'default' }, centerX: false, centerY: false, onUnblock:function () {
      dfd.reject();
    } });
    
    $('.blockOverlay').click(function() {
      th.hidePopup(dialog);
    });
    $('.dialog-close', dialog).unbind().click(function () {
      th.hidePopup(dialog);
    });
    $('.dialog-buttons-ok', dialog).unbind().click(function () {
      if (callback) {
        if (callback() !== false) {
          dfd.resolve();
          th.hidePopup(dialog);
        }
      } else {
        dfd.resolve();
        th.hidePopup(dialog);
      }
    });
    return dfd.promise();
  },
  hidePopup: function() {
    location.hash = '#/';
    $(document.body).unblock();
  },
  getPokecode: function(pokedex, forme) {
    forme = parseInt(forme || 0);
    pokedex = parseInt(pokedex);
    return PGL.Utils.zerofill((0x159a55e5 * (pokedex + forme * 0x10000) & 0xFFFFFF).toString(16), 6);
  },
  getCanonType: function(type) {
    if (!this.canonTypeList) {
      var t = {};
      t['ノーマル'] = t['Normal'] = t['Normal']= t['Normale'] = t['Normal'] = t['Normal'] = t['노말'] = 'normal';
      t['ほのお'] = t['Fire'] = t['Feu']= t['Fuoco'] = t['Feuer'] = t['Fuego'] = t['불꽃'] = 'fire';
      t['みず'] = t['Water'] = t['Eau']= t['Acqua'] = t['Wasser'] = t['Agua'] = t['물'] = 'water';
      t['でんき'] = t['Electric'] = t['Électrik']= t['Elettro'] = t['Elektro'] = t['Eléctrico'] = t['전기'] = 'electric';
      t['くさ'] = t['Grass'] = t['Plante']= t['Erba'] = t['Pflanze'] = t['Planta'] = t['풀'] = 'grass';
      t['こおり'] = t['Ice'] = t['Glace']= t['Ghiaccio'] = t['Eis'] = t['Hielo'] = t['얼음'] = 'ice';
      t['かくとう'] = t['Fighting'] = t['Combat']= t['Lotta'] = t['Kampf'] = t['Lucha'] = t['격투'] = 'fighting';
      t['どく'] = t['Poison'] = t['Poison']= t['Veleno'] = t['Gift'] = t['Veneno'] = t['독'] = 'poison';
      t['じめん'] = t['Ground'] = t['Sol']= t['Terra'] = t['Boden'] = t['Tierra'] = t['땅'] = 'ground';
      t['ひこう'] = t['Flying'] = t['Vol']= t['Volante'] = t['Flug'] = t['Volador'] = t['비행'] = 'flying';
      t['エスパー'] = t['Psychic'] = t['Psy']= t['Psico'] = t['Psycho'] = t['Psíquico'] = t['에스퍼'] = 'psychic';
      t['むし'] = t['Bug'] = t['Insecte']= t['Coleott.'] = t['Käfer'] = t['Bicho'] = t['벌레'] = 'bug';
      t['いわ'] = t['Rock'] = t['Roche']= t['Roccia'] = t['Gestein'] = t['Roca'] = t['바위'] = 'rock';
      t['ゴースト'] = t['Ghost'] = t['Spectre']= t['Spettro'] = t['Geist'] = t['Fantasma'] = t['고스트'] = 'ghost';
      t['ドラゴン'] = t['Dragon'] = t['Dragon']= t['Drago'] = t['Drachen'] = t['Dragón'] = t['드래곤'] = 'dragon';
      t['あく'] = t['Dark'] = t['Ténèbres']= t['Buio'] = t['Unlicht'] = t['Siniestro'] = t['악'] = 'dark';
      t['はがね'] = t['Steel'] = t['Acier']= t['Acciaio'] = t['Stahl'] = t['Acero'] = t['강철'] = 'steel';
      this.canonTypeList = t;
    }
    return this.canonTypeList[type] || 'none';
  },
  wakeup: function() {
    var that = this;
    that.showDialog(PGL.Text.get('pgltop.wakeup.confirm'), { ok:function () {
      that.getApi('pgl.member.profile.pdw_end_by_pgl', {}, function () {
        that.showDialog(PGL.Text.get('pgltop.wakeup.complete'), { ok:function () {
          location.reload();
        } });
      }, true);
    }, back:true });
  },
  isLoggedIn: function () {
    return this.level > PGL.NOT_LOGGED_IN;
  }
};

//--------------------------------------------------- PGL.Utils
PGL.Utils = {
  packText: function(target) {
    if (target && target.length) {
      var targetWidth = target.width();
      var span = target.children('.pack-text');
      if (span.size() == 0) {
        span = target.wrapInner($('<span class="pack-text"></span>')).children('.pack-text');
      }
      span.css({'white-space':'nowrap', 'letter-spacing':'0'}).removeClass('smallfont');

      var size = parseInt(target.css('font-size')) || 12;
      for (var i=size; i>=10 && targetWidth < span.width(); i--) {
        span.css({ 'font-size':i+'px', 'letter-spacing':'-1px' });
      }
      if (targetWidth < span.width()) {
        span.addClass('smallfont');
        span.css({ 'font-size':size+'px', 'letter-spacing':'0' });
        for (var i=size; i>=10 && targetWidth < span.width(); i--) {
          span.css({ 'font-size':i+'px', 'letter-spacing':'-1px' });
        }
      }
    }
  },
  zerofill: function(str, len) {
    str = '0000000000000000' + str;
    return str.substr(str.length - len);
  },
  formatTime: function(time, options) {
    options = options || {};
    
    // parse
    if (typeof time != 'object') {
      if (isNaN(time)) {
        var match = /(\d+)\D(\d+)\D(\d+)(?:\D(\d+))?(?:\D(\d+))?(?:\D(\d+))?/.exec(time);
        time = new Date(match[1], match[2] - 1, match[3], match[4] || 0, match[5] || 0, match[6] || 0);
      } else {
        time = new Date(time * 1000);
      }
    }
    
    // tz convert
    if (options.tzoffset !== undefined) {
      var offset = { ja:9, en:0, fr:0, it:0, de:0, es:0, ko:9 }[PGL.language] - options.tzoffset;
      time.setTime(time.getTime() + offset * 60 * 60 * 1000);
    }
    
    // format preset
    var format = options.format || 'LONG';
    if (format == 'LONG' || format == 'SHORT' || format == 'DATE') {
      var f = { ja:'YY/MM/DD', en:'MM/DD/YY', fr:'DD/MM/YY', it:'DD/MM/YY', de:'DD.MM.YY', es:'DD-MM-YY', ko:'YY.MM.DD' }[PGL.language];
      if (format == 'LONG') {
        format = f.replace(/YY/, 'YYYY') + ' hh:mm';
      } else if (format == 'SHORT') {
        format = f + ' hh:mm';
      } else if (format == 'DATE') {
        format = f.replace(/YY/, 'YYYY');
      }
    }
    
    // append timezone
    if (options.appendTZ) {
      format += ' ' + { ja:'JST', en:'UTC', fr:'UTC', it:'UTC', de:'UTC', es:'UTC', ko:'KST' }[PGL.language];
    }
    
    // formatting
    return format
      .replace('YYYY', time.getFullYear())
      .replace('YY', ('' + time.getFullYear()).substr(2))
      .replace('MM', this.zerofill(time.getMonth() + 1, 2))
      .replace('DD', this.zerofill(time.getDate(), 2))
      .replace('hh', this.zerofill(time.getHours(), 2))
      .replace('mm', this.zerofill(time.getMinutes(), 2))
  },
  formatNumber: function (num) {
    var r = ('' + num).split('.');
    var intSep = { ja:',', en:',', fr:' ', it:'.', de:' ', es:(num < 10000 ? '' : ' '), ko:',' }[PGL.language];
    var fracSep = { ja:'.', en:'.', fr:',', it:',', de:',', es:',', ko:'.' }[PGL.language];
    r[0] = r[0].replace(/([0-9]+?)(?=(?:[0-9]{3})+(?:$|\.))/g, '$1' + intSep);
    return r.join(fracSep);
  },
  renderDSFont: function(fontname, str) {
    var t = {
      '⑧':'×', '⑨':'÷', '⑬':'...', '⑭':'♂', '⑮':'♀',
      '⑯':'♠', '⑰':'♣', '⑱':'♥', '⑲':'♦', '⑳':'★',
      '⑴':'◎', '⑵':'○', '⑶':'□', '⑷':'△', '⑸':'◇',
      '⑹':'♪', '⑺':'☀', '⑻':'☁', '⑼':'☂', '⑽':'☃'
    };
    return (str || '').replace(/[①②③④⑤⑥⑦⑩⑪⑫⑾⑿⒀⒁⒂⒃⒄⒅⒆⒇]/g, function (match) {
      return '<img src="/assets/global/images/' + fontname + '/' + match.charCodeAt().toString(16) + '.png" align="top"/>';
    }).replace(/[⑧⑨⑬⑭⑮⑯⑰⑱⑲⑳⑴⑵⑶⑷⑸⑹⑺⑻⑼⑽]/g, function (match) {
      return t[match];
    });
  },
  getAvatarImage: function(id, size) {
    var url = '/profile/assets/images/avatar/' + id + '.png';
    var img =  $('<img/>').attr({src: url});
    if (size) img.css({width: size, height: size});
    return img;
  },
  getWordlbattleStatusText: function (worldbattle_status) {
    var ws = worldbattle_status || {};
    var text = '';
    if (ws.status == 0) {
      text = PGL.Text.get('profile.gbu.competition_status.i');
    } else if (ws.status == 1 && ws.gpfentryflg == 1) {
      text = PGL.Text.get('profile.gbu.competition_status.a');
    } else if (ws.status == 1 && ws.wifimatchupstate == 1 && ws.gpfentryflg == 0) {
      text = PGL.Text.get('profile.gbu.competition_status.b');
    } else if (ws.status == 1 && ws.wifimatchupstate == 2 && ws.gpfentryflg == 0) {
      text = PGL.Text.get('profile.gbu.competition_status.c');
      text = text.replace(/\[(.*?)\]/g, function (match, group1) {
        return PGL.Utils.formatTime(worldbattle_status.open_date_from, { format:group1, tzoffset:0 });
      });
    } else if (ws.status == 3 && ws.wifimatchupstate == 2 && ws.gpfentryflg == 0) {
      text = PGL.Text.get('profile.gbu.competition_status.f');
    } else if (ws.status == 4 && ws.wifimatchupstate == 4 && ws.gpfentryflg == 0) {
      text = PGL.Text.get('profile.gbu.competition_status.d');
    } else if (ws.status == 4 && ws.wifimatchupstate == 5 && ws.gpfentryflg == 0) {
      text = PGL.Text.get('profile.gbu.competition_status.e');
    } else if (ws.status == 5) {
      text = PGL.Text.get('profile.gbu.competition_status.g');
    } else if (ws.status == 7) {
      text = PGL.Text.get('profile.gbu.competition_status.h');
    } else if (ws.status == 6) {
      text = PGL.Text.get('profile.gbu.competition_status.j');
    } else {
      text = PGL.Text.get('profile.gbu.competition_status.k');
    }
    return text;
  }
};

// -------------------------------------------------- PGL.PDW
PGL.PDW = function(member, level) {
  this.member = member;
  this.level = level;
  this.states = null;
}

PGL.PDW.INTERMISSION = 20 * 60 * 60;
PGL.PDW.RE_ENTER_DURATION = 60 * 60;
PGL.PDW.RELATION_DREAM_PAL = 'dreampal';
PGL.PDW.RELATION_PENDING_REQUEST  = 'pending';
PGL.PDW.RELATION_RECEIVED_REQUEST = 'received';

PGL.PDW.prototype = {
  getStates: function() {
    if (this.level < PGL.TRIAL) {
      return null;
    };

    if (this.states) {
      return this.states;
    }

    var member = this.member;
    var r = {
      status_top: '',
      status_profile: '', 
      pokemon_top: '', 
      pokemon_profile: '', 
      wakeup_visibility: false, 
      wakeup_enabled: false
    };

    var dl = member.is_downloaded == '0';
    var ps = parseInt(member.play_status);

    var remains = member.nextstart_remaintime - this.getElapsed();
    var can_re_enter = remains > PGL.PDW.INTERMISSION - PGL.PDW.RE_ENTER_DURATION;
    var can_enter    = remains <= 0;

    var enterable = can_re_enter || can_enter;

    if (this.level == PGL.TRIAL) {
      r.wakeup_visibility = 
      r.wakeup_enabled = false;
      if (member.first_flag == '0') {
        r.status_top = PGL.Text.get('global.pdwstatus.15');
        r.status_profile = PGL.Text.get('global.pdwstatus.12');
      } else {
        if (enterable) {
          r.status_top = PGL.Text.get('global.pdwstatus.6');
          r.status_profile = PGL.Text.get('global.pdwstatus.14');
          r.pokemon_top = '';
          r.pokemon_profile = PGL.Text.get('global.fennels_munna');
        } else {
          if (remains > 3600) {
            r.status_top = PGL.Text.get('global.pdwstatus.1').replace(/HH/, Math.ceil(remains / 3600));
          } else if (remains > 60) {
            r.status_top = PGL.Text.get('global.pdwstatus.2').replace(/MM/, Math.ceil(remains / 60));
          } else {
            r.status_top = PGL.Text.get('global.pdwstatus.3');
          }
          r.status_profile = PGL.Text.get('global.pdwstatus.4');
          r.pokemon_top = '';
          r.pokemon_profile = PGL.Text.get('global.fennels_munna');
        }
      }
    } else {
      if (dl && ps == 3) {
        r.status_top = PGL.Text.get('global.pdwstatus.11');
        r.status_profile = PGL.Text.get('global.pdwstatus.10');
        r.pokemon_top = member.pokemon_name;
        r.pokemon_profile = member.pokemon_name;
        r.wakeup_visibility = true;
        r.wakeup_enabled = false;
      } else if (!member.pokemon_name || member.sleeping_flag != '1') {
        r.status_top = PGL.Text.get('global.pdwstatus.9');
        r.status_profile = PGL.Text.get('global.pdwstatus.8');
        r.pokemon_top = '-';
      } else if (dl && ps == 0) {
        r.status_top = PGL.Text.get('global.pdwstatus.9');
        r.status_profile = PGL.Text.get('global.pdwstatus.8');
        r.pokemon_top = '-';
      } else if (dl && ps == 1) {
        if (enterable) {
          r.status_top = PGL.Text.get('global.pdwstatus.7');
          r.status_profile = PGL.Text.get('global.pdwstatus.15');
          r.pokemon_top = member.pokemon_name;
          r.pokemon_profile = member.pokemon_name;
          r.wakeup_visibility = true;
          r.wakeup_enabled = false;
        } else {
          if (remains > 3600) {
            r.status_top = PGL.Text.get('global.pdwstatus.1').replace(/HH/, Math.ceil(remains / 3600));
          } else if (remains > 60) {
            r.status_top = PGL.Text.get('global.pdwstatus.2').replace(/MM/, Math.ceil(remains / 60));
          } else {
            r.status_top = PGL.Text.get('global.pdwstatus.3');
          }
          r.status_profile = PGL.Text.get('global.pdwstatus.4');
          r.pokemon_top = member.pokemon_name;
          r.pokemon_profile = member.pokemon_name;
          r.wakeup_visibility = true;
          r.wakeup_enabled = false;
        }
      } else if (dl && ps == 2) {
        if (enterable) {
          r.status_top = PGL.Text.get('global.pdwstatus.5');
          r.status_profile = PGL.Text.get('global.pdwstatus.13');
          r.pokemon_top = member.pokemon_name;
          r.pokemon_profile = member.pokemon_name;
          r.wakeup_visibility = true;
          r.wakeup_enabled = true;
        } else {
          if (remains > 3600) {
            r.status_top = PGL.Text.get('global.pdwstatus.1').replace(/HH/, Math.ceil(remains / 3600));
          } else if (remains > 60) {
            r.status_top = PGL.Text.get('global.pdwstatus.2').replace(/MM/, Math.ceil(remains / 60));
          } else {
            r.status_top = PGL.Text.get('global.pdwstatus.3');
          }
          r.status_profile = PGL.Text.get('global.pdwstatus.4');
          r.pokemon_top = member.pokemon_name;
          r.pokemon_profile = member.pokemon_name;
          r.wakeup_visibility = true;
          r.wakeup_enabled = true;
        }
      } else {
        r.status_top = PGL.Text.get('global.pdwstatus.9');
        r.status_profile = PGL.Text.get('global.pdwstatus.8');
        r.pokemon_top = '-';
        r.pokemon_profile = '';
        r.wakeup_visibility = false;
      }
    }
    this.states = r;
    return r;

    /*
    if (this.level == PGL.TRIAL) {
      if (member.first_flag == '0') {
        result.status = PGL.Text.get('sleep.status.7'); // まだ遊んでいません
        result.pokemon = PGL.Text.get('sleep.status.1'); // ねむっているポケモンはいません
      } else {
        result.status = PGL.Text.get('sleep.status.8'); // 体験版で遊んでいます
        result.pokemon = PGL.Text.get('sleep.status.9'); // マコモのムンナ
        result.fennels_munna = true;
      }
    } else {
      if (member.pokemon_name && member.is_downloaded != '1' && member.play_status == '3') {
        result.pokemon = member.pokemon_name;
        result.status = PGL.Text.get('sleep.status.6'); // 起きる準備に入りました
      } else if (member.sleeping_flag != '1' || !member.pokemon_name || member.is_downloaded == '1' || member.play_status == '0' || member.play_status == '4') {
        result.status = PGL.Text.get('sleep.status.2'); // ポケモンをねむらせてください。
        result.pokemon = PGL.Text.get('sleep.status.1'); // ねむっているポケモンはいません
      } else {
        result.pokemon = member.pokemon_name;

        var remains = member.nextstart_remaintime - this.getElapsed();
        var can_re_enter = remains > PGL.PDW.INTERMISSION - PGL.PDW.RE_ENTER_DURATION;
        var can_enter    = remains <= 0;

        if (member.play_status == '3') {
          result.status = PGL.Text.get('sleep.status.6'); // 起きる準備に入りました
        } else if (!can_re_enter && !can_enter) {
          result.wakeup_visibility = true;
          result.wakeup_enabled = member.play_status != '1'; // play_status=1なら起こすボタンをグレー表示
          result.status = PGL.Text.get('sleep.status.4'); // アクセス受付時間待ちです
        } else if (member.play_status == '1') {
          result.wakeup_visibility = true; // 起こすボタンをグレー表示
          result.wakeup_enabled = false;
          if (member.first_flag == '0') {
            result.status = PGL.Text.get('sleep.status.7'); // まだ遊んでいません
          } else {
            result.status = PGL.Text.get('sleep.status.3'); // 遊ぶことができます
          }
        } else if (member.play_status == '2') {
          result.wakeup_visibility = true;
          result.wakeup_enabled = true;
          result.status = PGL.Text.get('sleep.status.5'); // ゆめを見ています
        }
      }
    }
    this.states = result;
    return result;
    */
  },
  getElapsed: function () {
    return (new Date().getTime() - PGL.pageStartedAt) / 1000;
  }
};

// -------------------------------------------------- PGL.Host
PGL.Host = function() {
  this.string = location.hostname.replace(/(ja|en|fr|it|de|es|ko)\./,'*.');
  this.code = this.getHash(this.string);
}

PGL.Host.prototype = {
  getHash: function(s, size) {
    var b = 27183, h = 0, a = 31415;
    size = size || 0x10000;
    for (var i=0; i<s.length; i++) {
      h = (a * h + s.charCodeAt(i)) % size;
      a = (a % size) * (b % size) % size;
    }
    return h;
  },
  decrypt: function(ope, s) {
    s = s || this.string
    return $.map(ope.split(','), function(c) {
      var o = c.split(':');
      return o[1] ? String.fromCharCode(s.charCodeAt(o[0]) + parseInt(o[1])) : s.charAt(o[0]);
    }).join('');
  },
  getPdcDomain: function() {
    switch (this.code) {
      case  2918: return 'www.pokemon.jp';
      case 46003: return this.decrypt('6,18:3,9,3:73,8:-2,9,13:74,5,6,7,8,9,10,7,12,5,16:60,6');
      case 35561: return this.decrypt('0,1,2,0,17:3,6,7,8,9,1,11,8,13,6,1:5,7');
      case 20358: return 'dev4pdc.pokemon.jp';
      case 38736: return this.decrypt('0,1,2,9:-49,6,0,17,5,6,7,8,1,10,7,12,5,16:60,6');
      case 30582: return this.decrypt('24:-21,3,28:2,13:-49,0,35:-9,20,9,0,1,2,3,4,1,6,9,2:-1,0');
      case 55647: return 'dev4pdc.pokemon.jp';
    }
  },
  getComDomain: function() {
    switch (this.code) {
      case  2918: return 'www.pokemon.com';
      case 46003: return this.decrypt('0,1,17:-2,2,9,0,13:60,1,9,5,6,7,8,9,10,7,12,5,17,7,10');
      case 35561: return this.decrypt('2,0,3:-19,15,1,2,16:-3,0,1,6,7,8,9,1,11,8,13,6,18,8,11');
      case 38736: return this.decrypt('14:13,1,1:14,4:74,7:4,5:59,13:71,1,5,6,7,8,1,10,7,12,5,17,7,10');
      case 30582: return this.decrypt('17,3,12,17,12,27:-10,17,3,9,0,1,2,3,4,1,6,9,20,1,4');
    }
  },
  getPkiDomain: function() {
    switch (this.code) {
      case  2918: return 'pokemonkorea.co.kr';
      case 46003: return this.decrypt('0,1,2,5,6,7,8,9,10,7,12,8,7,12:4,9,16:51,5,17,7,5,8,2:11');
      case 35561: return this.decrypt('17:54,1,10:17,6,7,8,9,1,11,8,13,9,8,17:68,1,16:-11,6,18,8,6,9,15:11');
      case 38736: return this.decrypt('19:7,1,8:8,1:15,5,6,7,8,1,10,7,12,8,7,15:6,1,15:-11,5,17,7,5,8,17:15');
      case 30582: return this.decrypt('17,3,12,17,9,0,1,2,3,4,1,6,2,1,23,3,11,9,20,1,9,2,23');
    }
  },
  getPdcLoginUrl: function() {
    var result = { check: 'http://' + this.getPdcDomain() + '/portal/chkoperation.gif' };
    if (this.code == 2918) {
      result.check = [ 'http://www.pokemon.jp/check.gif', 'https://members.pokemon.jp/check.gif' ];
      result.form = 'https://' + this.decrypt('3:8,14:8,13:20,1,2,3,4,5,6,3,8,1,4:-1,2') + '/login/pgl.html';
    } if (this.code == 46003) {
      result.check = [
        'http://' + this.decrypt('6,7:3,9,10:-59,5,6,7,8,9,10,7,12,5,17:7,6') + '/check.gif',
        'https://' + this.decrypt('10,9,10,10:-11,9,5:68,0,3,0,1,2,5,6,7,8,9,10,7,12,5,13:61,6') + '/check.gif'
      ];
      result.form = 'https://' + this.decrypt('6,6:2,9,1:-66,5,6,7,8,9,10,7,12,5,7:-5,6') + '/login/pgl.html';
    } else if (this.code == 35561) {
      result.check = [
        'http://' + this.decrypt('7,18:15,1,10:-51,6,7,8,9,1,11,8,13,6,4:61,7') + '/check.gif',
        'https://' + this.decrypt('11,1,11,11:-11,1,11:5,2,4,2,0,15,6,7,8,9,1,11,8,13,6,1:5,7') + '/check.gif'
      ];
      result.form = 'https://' + this.decrypt('7,11:5,1,18:-49,6,7,8,9,1,11,8,13,6,15:3,7') + '/login/pgl.html';
    } else if (this.code == 38736) {
      result.check = [
        'http://' + this.decrypt('19:6,17:17,14,1:-51,5,6,7,8,1,10,7,12,5,8:-1,6') + '/check.gif',
        'https://' + this.decrypt('10,1,10,14:-5,1,18:3,12:5,3,11:5,1,17:16,17:17,5,6,7,8,1,10,7,12,5,5:60,6') + '/check.gif'
      ];
      result.form = 'https://' + this.decrypt('17:16,15:8,14,8:-57,5,6,7,8,1,10,7,12,5,2:-12,6') + '/login/pgl.html';
    } else {
      result.form = 'https://' + this.getPdcDomain() + '/login/pgl.html';
    }
    return result;
  },
  getComLoginUrl: function() {
    var result = { check: 'https://' + this.getComDomain() + '/pglcheck' };
    var cc = { en: 'us' }[ PGL.language ] || PGL.language;
    var c = 'https://' + this.getComDomain() + '/';
    var so = this.code == 2918 ? 'https://sso.pokemon.com/' : c;
    result.form = c + cc + '/account/logout?next=' + encodeURIComponent(so + 'sso/login?service=' + c + cc +  '/account/pgllogin&locale=' + PGL.language + '&renew=true');
    return result;
  },
  getPkiLoginUrl: function() {
    var c = 'http://' + this.getPkiDomain() + '/pgl/';
    return { check: c + 'chkoperation.gif', form: c + 'login_pgl.asp' };
  },
  getSwfHost: function() {
    switch (this.code) {
      case  2918:
      case 46003:
      case 35561:
        return 'cdn2.pokemon-gl.com';
      case 20358:
      case 38736:
      case 30582:
      default:
        return location.host;
    }
  },
  getPageAssetHost: function() {
    switch (this.code) {
      case  2918:
      case 46003:
        return 'cdn2.pokemon-gl.com';
      case 35561:
      case 20358:
      case 38736:
      case 30582:
      default:
        return location.host;
    }
  },
  getCmsImageHost: function() {
    switch (this.code) {
      case  2918:
        return 'cdn2.pokemon-gl.com';
      case 46003:
      case 35561:
      case 20358:
      case 38736:
      case 30582:
      default:
        return location.host;
    }
  }
};

// ------------------------------------------------ PGL.Text
PGL.Text = {
  get: function(sid, lang) {
    try {
      return PGL.Text.data[sid][lang || PGL.language];
    } catch (e) {
      return sid;
    }
  },
  add: function(data) {
    PGL.Text.data = PGL.Text.data || {}; 
    PGL.Text.data = $.extend(PGL.Text.data, data);
  }
}

PGL.Text.add({
  "error.load_error": {
    de: "Ein Fehler ist aufgetreten.",
    en: "An error occurred during data processing.",
    es: "Se ha producido un error mientras se estaban procesando los datos.",
    fr: "Une erreur s'est produite.",
    it: "Errore nella fase di elaborazione dei dati.",
    ja: "データの処理中にエラーが発生しました。",
    ko: "데이터 처리 중 에러가 발생했습니다."
  },
  'last_upload_time': {
    de:"DD.MM um hh:mm Uhr",
    en:"MM/DD hh:mm",
    es:"DD/MM a las hh:mm",
    fr:"hh:mm le DD/MM",
    it:"DD/MM hh:mm",
    ja:"MM/DD hh:mm",
    ko:"MM/DD hh:mm"
  }
});

// ------------------------------------------------ VolumeController-Content Interface
window.setVolume = function (volume) {
};

// ------------------------------------------------
$(function() { new PGL(); });
$(window).unload(function() {}); // fix firefox5 page-recycle-behavior


(function () {
  var squeezeTextQueue;
  $.fn.extend({
    squeezeText: function (text, targetWidth) {
      if (this.length > 1) {
        $.each(this, function () {
          $(this).squeezeText(text, targetWidth);
        });
      } else if (this.parent().length) {
        if (arguments.length > 0) {
          this.text(text);
        }
        if (this.is(':hidden')) {
          if (!squeezeTextQueue) {
            squeezeTextQueue = $();
            setInterval(function () {
              squeezeTextQueue.filter(':visible').each(function () {
                squeezeTextQueue = squeezeTextQueue.not(this);
                $(this).squeezeText();
              });
            }, 200);
          }
          squeezeTextQueue = squeezeTextQueue.add(this);
        } else {
          if (targetWidth == undefined) {
            targetWidth = this.width();
          }
          var span = this.children('.squeeze-text');
          if (span.length == 0) {
            span = this.wrapInner($('<span class="squeeze-text"></span>')).children('.squeeze-text');
          }
          span.css({ 'white-space':'nowrap' });
          for (var ls=parseInt(this.css('letter-spacing')) || 0; ls>=1 && targetWidth < span.width(); ls--) {
            span.css({ 'letter-spacing':ls });
          }
          
          for (var fs=parseInt(this.css('font-size')) || 12; fs>=10 && targetWidth < span.width(); fs--) {
            span.css({ 'font-size':fs });
          };
          for (; ls>=-1 && targetWidth < span.width(); ls--) {
            span.css({ 'letter-spacing':ls });
          }
          span.css({ 'white-space':'' });
        }
      }
      return this;
    },
    stopAll: function () {
      var hooks = jQuery._data(this.get(0), 'fx.run');
      if (hooks && hooks.stop) {
        hooks.stop(true);
      }
      return this.stop(true, true);
    },
    caret: function (index) {
      var elem = this.get(0);
      if (index == null) {
        if ($.browser.msie) {
          elem.focus();
          var range = document.selection.createRange();
          range.moveStart('character', -elem.value.length);
          return range.text.length;
        } else if (elem.selectionStart || elem.selectionStart == '0') {
          return elem.selectionStart;
        }
      }
      if (elem.createTextRange) {
        var range = elem.createTextRange();
        range.collapse(true);
        range.moveEnd('character', index);
        range.moveStart('character', index);
        range.select();
      } else if (elem.setSelectionRange) {
        elem.focus();
        elem.setSelectionRange(index, index);
      }
      return this;
    }
  });
})();



