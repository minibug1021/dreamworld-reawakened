var iscampaign = false;
var returnValue = "未設定です"; 

function setCampaignAlert( str )
{
	returnValue = str;
};

function setCampaign( bool )
{
	iscampaign = bool;
};

window.onbeforeunload = function(event)
{
	if ( iscampaign )
	{
		event = event || window.event;
		return event.returnValue = returnValue;
	}
};