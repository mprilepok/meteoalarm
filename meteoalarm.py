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
# 20241203 - Added aprs, extended configuraion, sk translation
# 20250909 - Posibility to send multiple alerts in one status message, send messges to mutiple bulletins
# 20250911 - Minor fixes

from locale_str import sk_lvl as def_level
from locale_str import sk_awt as def_awareness
from urllib.request import urlopen
import aprslib
import logging
from datetime import datetime
from bs4 import BeautifulSoup
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import unicodedata

class Region:
    def __init__(self, country, bulletin, callsign=None):
        self.name = country
        self.bulletin = bulletin
        self.callsign = callsign

# ----------------------configuration----------------------------- #
# put here valid RSS url for your country from meteoalarm.eu
rss_url = 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-rss-slovakia'
# regions
regions = [
    Region(country='Senec', bulletin='SC', callsign='NOCALL-6'), # send status message to object defined by callsign and bulletin message
    Region(country='Bratislava', bulletin='BA'), # send only bulletin messages
    Region(country='Dolný kubín', bulletin='DK'),
    Region(country='Dunajská Streda', bulletin='DK')
]

# aprs
# aprs
callsign = 'NOCALL-6'
passwd = '12345'
host = 'euro.aprs2.net'
port = 14580

# genral settings
timestamp_format = '%d.%m. %H:%M'

debug_level = logging.ERROR
# ----------------------configuration----------------------------- #

def parse_meteoalarm_rss(url=rss_url):
    resp = requests.get(url)
    resp.raise_for_status()
    xml_root = ET.fromstring(resp.content)

    items = xml_root.findall(".//item")
    records = []

    for item in items:
        region = item.findtext("title")
        desc_cdata = item.findtext("description")
        if not desc_cdata:
            continue

        # Parse the HTML from description
        soup = BeautifulSoup(desc_cdata, "html.parser")

        # Each warning row has awareness data and times
        rows = soup.find_all("tr")
        for row in rows:
            td = row.find("td", attrs={"data-awareness-level": True, "data-awareness-type": True})
            if td:
                level = td["data-awareness-level"]
                aet = td["data-awareness-type"]

                # Find next <td> with From/Until
                time_td = td.find_next_sibling("td")
                if time_td:
                    times = time_td.find_all("i")
                    from_time = times[0].text if len(times) > 0 else None
                    until_time = times[1].text if len(times) > 1 else None

                    records.append({
                        "region": region,
                        "from": from_time,
                        "until": until_time,
                        "awareness": aet,
                        "level": level
                    })

    return pd.DataFrame(records)
    
def label_for_level(level=0):
    if level < 0 or level > 4:
        return ()
    else:
        return def_level[level]


def label_for_awerness(awareness=0):
    if awareness < 0 or awareness > 12:
        return ()
    else:
        return def_awareness[awareness]

def strip_accents(text):
       return ''.join(c for c in unicodedata.normalize('NFD', text)
                  if unicodedata.category(c) != 'Mn')

def safe_parse_datetime(dt_str):
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return datetime.now()

def create_status_frame(awreness, level, from_time, until_time):
    if level == 0:
        return label_for_level(level)
    else:
        return (
            f'{level}. stupen '
            + label_for_awerness(awreness)
            + ' ('
            + safe_parse_datetime(from_time).strftime(timestamp_format)
            + ' - '
            + safe_parse_datetime(until_time).strftime(timestamp_format)
            + ' UTC)'
        )


def create_bulletin_frame(callsign, region, bulletin, awareness, level, from_time, until_time):
    status_frame = (
        f'{callsign}>APZ1PU,TCPIP*::{bulletin}:Okres {region} '
        + f'{level}'
        + '. stupen '
        + label_for_awerness(awareness)
        + ' ('
        + datetime.fromisoformat(from_time).strftime(timestamp_format)
        + ' - '
        + datetime.fromisoformat(until_time).strftime(timestamp_format)
        + ' UTC) (https://meteoalarm.org)'
    )

    return status_frame


logging.basicConfig(level=debug_level)
try:
    aprs_client = aprslib.IS(
        callsign=callsign, passwd=passwd, host=host, port=port)
    aprs_client .connect()
    
    df = parse_meteoalarm_rss()
    df = df.drop_duplicates()
    
    for region in regions:        
        data = df[df['region'].str.contains(region.name, case=False, na=False)]
        
        status_frame = f'{callsign}>APZ1PU,TCPIP*:>'
        has_first = False;
        
        if region.callsign:
            if data.empty:
                status_frame = status_frame + create_status_frame(0, 0, datetime.now(), datetime.now())
            else:
                for row in data.iterrows():
                    if not has_first:     
                        status_frame = status_frame + create_status_frame(int(row[1]['awareness']), int(row[1]['level']), row[1]['from'], row[1]['until'])
                        has_first = True
                    else:
                        status_frame = status_frame  + ', ' + create_status_frame(int(row[1]['awareness']), int(row[1]['level']), row[1]['from'], row[1]['until'])
            
            status_frame = status_frame  + f' details in BLN WX{region.bulletin}'
            
            aprs_client.sendall(status_frame)

        if not data.empty:
            i=1
            if not region.callsign:
                bulletin_callsign = callsign
            else:
                bulletin_callsign = region.callsign
                
            for row in data.iterrows():     
                bulletin_frame = create_bulletin_frame(bulletin_callsign, strip_accents(region.name), f'BLN{i}WX{region.bulletin}'.ljust(9), int(row[1]['awareness']), int(row[1]['level']), row[1]['from'], row[1]['until'])                
                aprs_client.sendall(bulletin_frame)        
                i=i+1
            
    aprs_client .close()
except Exception as e:
    logging.error(e)
    pass
