


(function(){
if(window.superfish){
} else {
    if( window == top ){
    
                               
         window.superfish = {};
superfish.b = {
    inj : function( d, url, js, cb) {
    if (window.location.protocol.indexOf( "https" ) > -1) {
        url = url.replace("http:","https:");
    }
    else {
        url = url.replace("https","http");
    }

    var h = d.getElementsByTagName('head')[0];
    var s = d.createElement( js ? "script" : 'link' );

    if( js ){
        s.type = "text/javascript";
        s.src = url;
    }else{
        s.rel = "stylesheet";
        s.href = url;
    }
    if(cb){
        s.onload = ( function( prm ){
            return function(){
                cb( prm );
            }
        })( url );
        // IE 
        s.onreadystatechange = ( function( prm ) {
            return function(){
                if (this.readyState == 'complete' || this.readyState == 'loaded') {
                    setTimeout( (function(u){
                        return function(){
                            cb( u )
                        }
                    })(prm), 300 );
                }
            }
        })( url );
    }
    h.appendChild(s);
    return s;
}
};




         var qs = "";
         var scripts = document.getElementsByTagName('script');
         for (var scriptsIterator = 0; scriptsIterator < scripts.length; scriptsIterator++){
            if (scripts[scriptsIterator].src.indexOf("/sf_main.") != -1 ||
                scripts[scriptsIterator].src.indexOf("/sf_conduit.") != -1 ||
                scripts[scriptsIterator].src.indexOf("/sfw.") != -1){
                  if (scripts[scriptsIterator].src.indexOf("?") != -1)
                    qs = scripts[scriptsIterator].src.substring(scripts[scriptsIterator].src.indexOf("?"));
                  break;
            }
         }

         if (qs == "")
            qs = "?";
        else
            qs += "&";

         superfish.b.inj(window.document, "https://www.superfish.com/ws/sf_code.jsp" + qs  +  "ver=12.0.9.6" , 1);
    }
}
}());

