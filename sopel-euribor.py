import urllib
import xmltodict
from sopel import plugin


@plugin.command("euribor")
def get_euribor(bot, trigger):
    try:
        url = "https://www.suomenpankki.fi/WebForms/ReportViewerPage.aspx?report=/tilastot/markkina-_ja_hallinnolliset_korot/euribor_korot_today_xml_en&output=xml"
        file = urllib.request.urlopen(url)
        data = file.read()
        file.close()
        data = xmltodict.parse(data)
        euribor_rates = data["Report"]["data"]["period_Collection"]["period"][
            "matrix1_Title_Collection"
        ]["rate"]

        for euribor_rate in euribor_rates:
            if euribor_rate["@name"] == "12 month (act/360)":
                intr = euribor_rate["intr"]
                euribor_12_months = "Euribor 12kk: {}%".format(intr["@value"])
                bot.say(euribor_12_months)

    except Exception as e:
        bot.say("Ei onnistunu hakeminen, sori siitä!")
        print("Couldn't load euribor xml data, error: ", e)
