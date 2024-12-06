#!/usr/bin/python3

# Copyright (c) 2024 OM1PU Michal Prilepok
# Based on work SQ9MDD Rysiek Labus
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

# DATA SOURCE meteoalarm.eu
# look for metegram and find' img with alt='awt:6 level:1'
#   Awarness Type:
#   1       wind
#   2       snow / ice
#   3       thunderstorm
#   4       fog
#   5       extreme high temperature
#   6       extreme low temperature
#   7       coastal event
#   8       Forest fire
#   9       Avalanches
#   10      Rain
#   11      Flood
#   12      Rain-Flood

#   Awarness level:
#   0       No data or invalid data
#   1       GREEN No particular awareness of the weather is required
#   2       YELLOW The weather is potentially dangerous. The weather phenomena that have been forecast are not unusual, but be attentive if you intend to practice activities exposed to meteorological risks
#   3       ORANGE The weather is dangerous. Unusual meteorological phenomena have been forecast. Damage and casualties are likely to happen
#   4       RED The weather is very dangerous. Exceptionally intense meteorological phenomena have been forecast. Major damage and accidents are likely, in many cases with threat to life and limb, over a wide area.

# CHANGELOG
# 20241202 - fork from SQ9MDD Rysiek Labus repo
# 20241203 - Added aprs, extende configuraion, sk translation

from locale_str import sk_lvl as def_lvl
from locale_str import sk_awt as def_awt
from urllib.request import urlopen
import aprslib
import logging
from datetime import datetime
# ----------------------configuration----------------------------- #
# put here valid RSS url for your country from meteoalarm.eu
rss_url = 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-rss-slovakia'
# region or country name exactly as it is in RSS
rss_county = 'Senec'
# aprs
callsign = 'NOCALL-6'
passwd = '12345'
host = 'euro.aprs2.net'
bulletin_name = 'BLN1WXSC' # bulletin name for Senec
port = 14580
timestamp_format = '%d.%m. %H:%M'

debug_level = logging.ERROR
# ----------------------configuration----------------------------- #


def set_label_for_alert(alert=0):
    if alert < 0 and alert < 12:
        return ()
    else:
        return def_lvl[alert]


def set_label_for_awerness(awt=0):
    if awt < 0 and awt > 4:
        return ()
    else:
        return def_awt[awt]


def get_data_and_extract_alerts(rss_url, rss_county):
    try:
        response = urlopen(rss_url)
        text = response.read().decode('utf-8')
        county_code_pos = text.find(rss_county)
        awt_pos = text.find('awt:', county_code_pos) + 4
        lvl_pos = text.find('level:', county_code_pos) + 6
        from_pos = text.find('From:', county_code_pos) + 13
        until_pos = text.find('Until:', county_code_pos) + 14
        awt = text[awt_pos: (awt_pos + 2)]  # AWT
        lvl = text[lvl_pos: (lvl_pos + 1)]  # LVL
        from_time = text[from_pos: (from_pos + 25)]  # from_time
        until_time = text[until_pos: (until_pos + 25)]  # until_time

        # awt,lvl,from_time,until_time
        return_data = [int(awt), int(lvl), from_time, until_time]
        return return_data
    except:
        # awt,lvl,from_time,until_time
        return_data = [0, 0, '', '']
        return return_data


def create_status_frame(awt, lvl, from_time, until_time):
    status_frame = (
        f'{callsign}>APZ1PU,TCPIP*:>'
        + set_label_for_alert(lvl)
        + ' '
        + set_label_for_awerness(awt)
        + ' ('
        + datetime.fromisoformat(from_time).strftime(timestamp_format)
        + ' - '
        + datetime.fromisoformat(until_time).strftime(timestamp_format)
        + ' UTC) (https://meteoalarm.org)'
    )

    return status_frame


def create_bulletin_frame(awt, lvl, from_time, until_time):
    status_frame = (
        f'{callsign.ljust(9)}>APZ1PU,TCPIP*::{bulletin_name.ljust(9)}:Okres {rss_county} '
        + set_label_for_alert(lvl)
        + ' '
        + set_label_for_awerness(awt)
        + ' ('
        + datetime.fromisoformat(from_time).strftime(timestamp_format)
        + ' - '
        + datetime.fromisoformat(until_time, ).strftime(timestamp_format)
        + ' UTC) (https://meteoalarm.org)'
    )

    return status_frame


logging.basicConfig(level=debug_level)
try:
    aprs_client = aprslib.IS(
        callsign=callsign, passwd=passwd, host=host, port=port)
    aprs_client .connect()

    curr_alert_data = get_data_and_extract_alerts(rss_url, rss_county)

    if curr_alert_data[1] > 1:
        status_frame = create_status_frame(
            curr_alert_data[0], curr_alert_data[1], curr_alert_data[2], curr_alert_data[3])
    else:
        status_frame = f'{callsign}>APZ1PU,TCPIP*:' + \
            '>' + set_label_for_alert(curr_alert_data[1])

    aprs_client .sendall(status_frame)

    if curr_alert_data[1] > 1:
        status_frame = create_bulletin_frame(
            curr_alert_data[0], curr_alert_data[1], curr_alert_data[2], curr_alert_data[3])

        aprs_client .sendall(status_frame)

    aprs_client .close()
except Exception as e:
    logging.error(e)
    pass
