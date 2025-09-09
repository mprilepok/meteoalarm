# meteoalarm
A project to make meteo alert (https://www.meteoalarm.eu/) weather warning data available over the APRS network.
- captures and sends warnings for configured regions
- creates a status message to the existing WX Station (no beacon or weather data is sent)
- creates bulletin message
- multiple bulletin can be configured
 
## Requires
Aee requirements.txt.

## Install
```
pip install -r requirements.txt
```
## Configuration
### Regions
```
regions = [
    Region(country='Senec', bulletin='BLN1WXSC', callsign='OM1PU-6'), # send status message to object defined by callsign and bulletin message
    Region(country='Bratislava', bulletin='BLN1WXBA'), # send only bulletin messages
]
```
### APRS
```
# aprs
callsign = 'NOCALL-6' # callsign
passwd = '12345' # APRS pass code
host = 'euro.aprs2.net' # APRS server host
port = 14580 # APRS server port
```
## Run 
### From shell
```
python meteoalarm.py
```
### Cron example
```
/usr/bin/python3 /home/aprs/meteoalarm.py
```

# Todo
- [ ] Add APRS WX station beacon
- [x] Better data extraction
- [x] Better warning processing

# Credists and source
Based on work [SQ9MDD Rysiek Labus](https://github.com/SQ9MDD/meteoalarm)