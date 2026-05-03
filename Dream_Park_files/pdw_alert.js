var ispdw = false;
var returnValue = {
	"ja":"ポケモンを起こす場合は「ポケモンドリームワールドを終了」を押してください。",
	"ko":'포켓몬을 깨울 경우에는 「PDW를 종료한다」를 눌러주십시오. ',
	"fr":'Si vous voulez réveiller votre Pokémon, appuyez sur "Quitter le Pokémon Dream World". ',
	"es":'Para despertar a tu Pokémon, primero debes hacer clic en "Salir de Pokémon Dream World". ',
	"it":'Per risvegliare il Pokémon, scegli Esci dal Pokémon DW. ',
	"de":'Betätige „Pokémon DW beenden“, um deine Pokémon aufzuwecken. ',
	"en":'Leave the Pokémon Dream World to wake your Pokémon. '
};

function getLang() {
	return (location.href.match(/\W(ja|en|fr|it|de|es|ko)\./) || [null, "ja"])[1];
}
function setpdw(bool)
{
	ispdw = bool;
}
window.onbeforeunload = function(event)
{
	if (ispdw)
	{
		event = event || window.event;
		return event.returnValue = returnValue[getLang()];
	}
}