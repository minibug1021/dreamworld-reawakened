var iscustom = false;
var returnValue; 

function setCustomizeAlert( str )
{
	returnValue = str;
}

function setCustomize( bool )
{
	iscustom = bool;
}

window.onbeforeunload = function(event)
{
	if ( iscustom )
	{
		event = event || window.event;
		return event.returnValue = returnValue;
	}
}