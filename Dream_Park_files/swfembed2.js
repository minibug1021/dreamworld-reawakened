function login( path, str, ini ) 
{		
	var arr = window.location.href.split(".");
	
	if( arr[0].length == 9 ) {
		path = "http://cdn2.pokemon-gl.com" + path;
	}
	else {
		if( arr[0].indexOf( "dev2-" ) > 0 ) {
			path = "http://cdn2.pokemon-gl.com" + path;
		}
	}
	
	
	if (swfobject.hasFlashPlayerVersion("10.0.2"))
	{		

		var para = location.search;
		var s = para.split("&");
		var v = s[0].split("=");
		
		if( s.length > 1 ) {
			var q = s[1].split("=");
		}
		
		var vars1;
		if( v[0] == "?shortcut" ) {
			vars1 = v[1];
		}
		
		var vars2;
		if( v[0] == "?mailto" ) {
			vars2 = v[1];
		}
		
		var vars3;
		if( v[0] == "?rankingto" ) {
			vars3 = v[1];
		}
		
		var vars4;
		if( v[0] == "?infoto" ) {
			vars4 = v[1];
		}
		
		
		var flashvars = { shortcut:vars1, mailto:vars2, rankingto:vars3, infoto:vars4, api_host_name:"/api/", page:str, json:ini, v:"2.0", lang:window.location };
		var param = {
			allowFullScreen:"true",
			allowScriptAccess:"always",
			menu:"false",
			transparent:"opaque",
			scale:"noscale"
		};
		var attributes = { id:"flashcontent" };
		swfobject.embedSWF(
			path+"main.swf",
			"flashcontent",
			"1003",
			"528",
			"10.0.2",
			path+"expressInstall.swf",
			flashvars,
			param,
			attributes
		)

	}
	else if (swfobject.hasFlashPlayerVersion("6.0.65"))
	{
		// expressinstall
		var isIE  = (navigator.appVersion.indexOf("MSIE") != -1) ? true : false;
		var playerType = (isIE == true) ? "ActiveX" : "PlugIn";
		var redirectURL = window.location;
		document.title = document.title.slice(0, 47) + " - Flash Player Installation";
		var doctitle = document.title;
		var flashvars = {
			MMredirectURL:redirectURL,
			MMplayerType:playerType,
			MMdoctitle:doctitle
		};
		var param = {
			allowFullScreen:"true",
			allowScriptAccess:"always",
			menu:"false",
			transparent:"opaque",
			scale:"noscale"
		};
		var attributes = { id:"flashcontent" };
		swfobject.embedSWF(
			path+"playerinstall.swf",
			"flashcontent",
			"1003",
			"528",
			"6.0.65",
			path+"expressInstall.swf",
			flashvars,
			param,
			attributes
		)
	}
	else
	{
		// install flash player		
		$( "#plugin" ).css( "display", "block" );
	}
}
	
function thisMovie(movieName) {
	if (navigator.appName.indexOf("Microsoft") != -1) {
		return window[movieName];
	} else {
		return document[movieName];
	}
}

function setVolume(v){
	thisMovie("flashcontent").sendVolume(v);
}

function reload()
{
	location.reload();
}