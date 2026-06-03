This file documents changes that had to be made to the original .swf files in order to allow this standalone server to work.

## main.swf
### bfp.main.SoundController.as:23-29

```diff
- ExternalInterface.addCallback("sendVolume",this.receivedFromJavaScript);

+ try
+ {
+     ExternalInterface.addCallback("sendVolume",this.receivedFromJavaScript);
+ }
+     catch(e:Error)
+ {
+ }
```

### bfp.common.PokemonBridge.as:461-462

```diff
+ PDW_API = "http://127.0.0.1:8080/api/";
+ PDW_API_SSL = "http://127.0.0.1:8080/api/";
```

### bfp.common.textFieldManager.as:350

```diff
- _loc2_ = "";

+ _loc2_ = param1;
```

## pdw_home.swf

### bfp.tpc.pdw.home.Home.as:630-640

```diff
+ if(!data["member" + PokemonBridge.member_id]["tutorial0"])
+ {
+     i = 0;
+     while(i <= 11)
+     {
+         data["member" + PokemonBridge.member_id]["tutorial" + i] = true;
+         trace(data["member" + PokemonBridge.member_id]["tutorial" + i]);
+         i++;
+     }
+     PDWSharedObject.save(data);
+ }
```