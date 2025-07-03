# GNSS Module
Er is gekozen voor de [LC76G van waveshare](https://www.waveshare.com/wiki/LC76G_GNSS_Module). [Halverwege de pagina](https://www.waveshare.com/wiki/LC76G_GNSS_Module#:~:text=as%20shown%20below%3A-,Working%20With%20Raspberry%20Pi) staat de bijbehorende code.

Voor het opzetten is hier niet gebruik van gemaakt. In plaats hiervan is [deze post](https://austinsnerdythings.com/2021/04/19/microsecond-accurate-ntp-with-a-raspberry-pi-and-pps-gps/) gevolgd, en [de nieuwere versie van de post](https://austinsnerdythings.com/2025/02/14/revisiting-microsecond-accurate-ntp-for-raspberry-pi-with-gps-pps-in-2025/). Bij het volgen zijn deze stappen aangepast:
* standaard baud rate is op 115200 gezet in plaats van 9600
* config.txt is te vinden onder /boot/firmware/, niet onder /boot/
* het gebruik van `sudo rpi-update` is overgeslagen. Hierdoor veranderd de eerste 

Als ook de locatie gebruikt wil worden, moet er goed gekeken worden naar [welk format](https://support.google.com/maps/answer/18539?hl=en&co=GENIE.Platform%3DDesktop#:~:text=Format%20your%20coordinates%20so%20they%20work%20in%20Google,your%20longitude%20coordinate%20is%20between%20-180%20and%20180.) de GNSS module gebruikt. Bij een verkeerd interpreteren van het format lijkt de GNSS module een verkeerde locatie te geven.

Crony zal zelfstandig detecteren of een GNSS module is aangesloten en of deze bruikbare data doorstuurt naar de Pi. Het kan tot 20 minuten duren voordat crony de NMEA en PPS data van de GNSS module adopteerd als tijdbron. Of dit al het geval is kan gecontroleerd worden met:
```bash
gpsmon
```
Of
```bash
cgps
```