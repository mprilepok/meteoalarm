# meteoalarm
A project to make meteo alert (https://www.meteoalarm.eu/) weather warning data available over the APRS network.
- captures and sends first warning
- creates a status message to the existing WX Station (no beacon or weather data is sent)
- creates bulletin message
 
## Requires
- [aprslib 0.7.2](https://pypi.org/project/aprslib/)

## Install
```
pip install -r requirements.txt
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
- [ ] Better data extraction
- [ ] Better warning processing

# Credists and source
Based on work [SQ9MDD Rysiek Labus](https://github.com/SQ9MDD/meteoalarm)