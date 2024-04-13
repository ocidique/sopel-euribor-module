import urllib
import xmltodict
from datetime import datetime, timedelta
from sopel import plugin


@plugin.command("euribor")
def get_euribor(bot, trigger):
    try:
        url = "https://www.suomenpankki.fi/WebForms/ReportViewerPage.aspx?report=/tilastot/markkina-_ja_hallinnolliset_korot/euribor_korot_xml_short_fi&output=xml"
        file = urllib.request.urlopen(url)
        data = file.read()
        file.close()
        data = xmltodict.parse(data)

        periods = data["Report"]["data"]["period_Collection"]["period"]

        """ Latest period """
        latest_period = next(iter(periods))
        # Convert latest period date str as datetime value for further usage
        latest_date = convert_date_str_to_datetime(latest_period["@value"])

        # Get previous valid values since euribor rates are missing weekends in the API
        """ Previous weekday """
        prev_day = latest_date - timedelta(days=1)
        prev_day_valid = get_valid_next_period_value(
            periods, convert_datetime_to_date_str(prev_day)
        )

        """ Previous week """
        prev_week = latest_date - timedelta(days=7)
        prev_week_day_valid = get_valid_next_period_value(
            periods, convert_datetime_to_date_str(prev_week)
        )

        """ Previous month """
        prev_month = latest_date.replace(month=latest_date.month - 1)
        prev_month_day_valid = get_valid_next_period_value(
            periods, convert_datetime_to_date_str(prev_month)
        )

        """ Previous year """
        prev_year = latest_date.replace(year=latest_date.year - 1)
        prev_year_day_valid = get_valid_next_period_value(
            periods, convert_datetime_to_date_str(prev_year)
        )

        euribor_12_month_latest = ""
        euribor_12_month_prev_day = ""
        euribor_12_month_prev_week = ""
        euribor_12_month_prev_month = ""
        euribor_12_month_prev_year = ""

        for period in periods:
            if period["@value"] == latest_period["@value"]:
                euribor_12_month_latest += str(
                    get_euribor_12_month_rate(period["col_grp_currency_Collection"])
                )
            elif period["@value"] == prev_day_valid["@value"]:
                euribor_12_month_prev_day += str(
                    get_euribor_12_month_rate(period["col_grp_currency_Collection"])
                )
            elif period["@value"] == prev_week_day_valid["@value"]:
                euribor_12_month_prev_week += str(
                    get_euribor_12_month_rate(period["col_grp_currency_Collection"])
                )
            elif period["@value"] == prev_month_day_valid["@value"]:
                euribor_12_month_prev_month += str(
                    get_euribor_12_month_rate(period["col_grp_currency_Collection"])
                )
            elif period["@value"] == prev_year_day_valid["@value"]:
                euribor_12_month_prev_year += str(
                    get_euribor_12_month_rate(period["col_grp_currency_Collection"])
                )

        say_str = "Euribor 12kk: {}%, eilen: {}, vko sit: {}, kk sit: {}, vuos sit: {}".format(
            euribor_12_month_latest,
            format_final_value(euribor_12_month_latest, euribor_12_month_prev_day),
            format_final_value(euribor_12_month_latest, euribor_12_month_prev_week),
            format_final_value(euribor_12_month_latest, euribor_12_month_prev_month),
            format_final_value(euribor_12_month_latest, euribor_12_month_prev_year),
        )

        bot.say(say_str)

    except Exception as e:
        bot.say("Ei onnistunu hakeminen, sori siitä!")
        print("Couldn't load euribor xml data, error: ", e)


def format_final_value(latest_value: str, compared_value: str) -> str:
    if float(latest_value.replace(",", ".")) > float(compared_value.replace(",", ".")):
        compared_value += str("% ")
        compared_value += str("\U0001f4c8")  # chart with upwards trend
    else:
        compared_value += str("% ")
        compared_value += str("\U0001f4c9")  # chart with downwards trend

    return compared_value


def convert_date_str_to_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d")


def convert_datetime_to_date_str(value: datetime) -> str:
    return value.strftime("%Y-%m-%d")


def get_valid_next_period_value(periods: list, value: str) -> str:
    valid_date = None
    check_value = value
    while valid_date is None:
        valid_date = next(
            (item for item in periods if item["@value"] == check_value), None
        )
        date_value = convert_date_str_to_datetime(check_value)
        date_value -= timedelta(days=1)
        check_value = convert_datetime_to_date_str(date_value)

    return valid_date


def get_euribor_12_month_rate(rates: list) -> str:
    for rate in rates["rate"]:
        if rate["@name"] == "12 kk (tod.pv/360)":
            return rate["intr"]["@value"]
