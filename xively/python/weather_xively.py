#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import sys
import time
import math
import logging as log
import httplib
import json
import threading
log.basicConfig(level=log.INFO)

from tinkerforge.ip_connection import IPConnection
from tinkerforge.ip_connection import Error
from tinkerforge.brick_master import Master
from tinkerforge.bricklet_lcd_20x4 import LCD20x4
from tinkerforge.bricklet_ambient_light import AmbientLight
from tinkerforge.bricklet_ambient_light_v2 import AmbientLightV2
from tinkerforge.bricklet_humidity import Humidity
from tinkerforge.bricklet_barometer import Barometer

class Xively:
    HOST = 'api.xively.com'
    AGENT = "Tinkerforge xively 1.0"
    FEED = '105813.json'
    API_KEY = 'WtXx2m6ItNZyFYoQyR5qnoN1GsOSAKxPMGdIaXRLYzY5ND0g'

    def __init__(self):
        self.items = {}
        self.headers = {
            "Content-Type"  : "application/x-www-form-urlencoded",
            "X-ApiKey"      : Xively.API_KEY,
            "User-Agent"    : Xively.AGENT,
        }
        self.params = "/v2/feeds/" + str(Xively.FEED)
        self.upload_thread = threading.Thread(target=self.upload)
        self.upload_thread.daemon = True
        self.upload_thread.start()

    def put(self, identifier, value):
        try:
            _, min_value, max_value = self.items[identifier]
            if value < min_value:
                min_value = value
            if value > max_value:
                max_value = value
            self.items[identifier] = (value, min_value, max_value)
        except:
            self.items[identifier] = (value, value, value)

    def upload(self):
        while True:
            time.sleep(5*60) # Upload data every 5min
            if len(self.items) == 0:
                continue

            stream_items = []
            for identifier, value in self.items.items():
                stream_items.append({'id': identifier,
                                     'current_value': value[0],
                                     'min_value': value[1],
                                     'max_value': value[2]})

            data = {'version': '1.0.0',
                    'datastreams': stream_items}
            self.items = {}
            body = json.dumps(data)

            try:
                http = httplib.HTTPSConnection(Xively.HOST)
                http.request('PUT', self.params, body, self.headers)
                response = http.getresponse()
                http.close()

                if response.status != 200:
                    log.error('Could not upload to xively -> ' +
                              str(response.status) + ': ' + response.reason)
            except Exception as e:
                log.error('HTTP error: ' + str(e))

class WeatherStation:
    HOST = "localhost"
    PORT = 4223

    ipcon = None
    lcd = None
    al = None
    al_v2 = None
    hum = None
    baro = None

    def __init__(self):
        self.xively = Xively()
        self.ipcon = IPConnection()
        while True:
            try:
                self.ipcon.connect(WeatherStation.HOST, WeatherStation.PORT)
                break
            except Error as e:
                log.error('Connection Error: ' + str(e.description))
                time.sleep(1)
            except socket.error as e:
                log.error('Socket error: ' + str(e))
                time.sleep(1)

        self.ipcon.register_callback(IPConnection.CALLBACK_ENUMERATE,
                                     self.cb_enumerate)
        self.ipcon.register_callback(IPConnection.CALLBACK_CONNECTED,
                                     self.cb_connected)

        while True:
            try:
                self.ipcon.enumerate()
                break
            except Error as e:
                log.error('Enumerate Error: ' + str(e.description))
                time.sleep(1)

    def cb_illuminance(self, illuminance):
        if self.lcd is not None:
            text = 'Illuminanc %6.2f lx' % (illuminance/10.0)
            self.lcd.write_line(0, 0, text)
            self.xively.put('AmbientLight', illuminance/10.0)
            log.info('Write to line 0: ' + text)

    def cb_illuminance_v2(self, illuminance):
        if self.lcd is not None:
            text = 'Illumina %8.2f lx' % (illuminance/100.0)
            self.lcd.write_line(0, 0, text)
            self.xively.put('AmbientLight', illuminance/100.0)
            log.info('Write to line 0: ' + text)

    def cb_humidity(self, humidity):
        if self.lcd is not None:
            text = 'Humidity   %6.2f %%' % (humidity/10.0)
            self.lcd.write_line(1, 0, text)
            self.xively.put('Humidity', humidity/10.0)
            log.info('Write to line 1: ' + text)

    def cb_air_pressure(self, air_pressure):
        if self.lcd is not None:
            text = 'Air Press %7.2f mb' % (air_pressure/1000.0)
            self.lcd.write_line(2, 0, text)
            self.xively.put('AirPressure', air_pressure/1000.0)
            log.info('Write to line 2: ' + text)

            temperature = self.baro.get_chip_temperature()/100.0
            # \xDF == ° on LCD 20x4 charset
            text = 'Temperature %5.2f \xDFC' % temperature
            self.lcd.write_line(3, 0, text)
            self.xively.put('Temperature', temperature)
            log.info('Write to line 3: ' + text.replace('\xDF', '°'))

    def cb_enumerate(self, uid, connected_uid, position, hardware_version,
                     firmware_version, device_identifier, enumeration_type):
        if enumeration_type == IPConnection.ENUMERATION_TYPE_CONNECTED or \
           enumeration_type == IPConnection.ENUMERATION_TYPE_AVAILABLE:
            if device_identifier == LCD20x4.DEVICE_IDENTIFIER:
                try:
                    self.lcd = LCD20x4(uid, self.ipcon)
                    self.lcd.clear_display()
                    self.lcd.backlight_on()
                    log.info('LCD 20x4 initialized')
                except Error as e:
                    log.error('LCD 20x4 init failed: ' + str(e.description))
                    self.lcd = None
            elif device_identifier == AmbientLight.DEVICE_IDENTIFIER:
                try:
                    self.al = AmbientLight(uid, self.ipcon)
                    self.al.set_illuminance_callback_period(1000)
                    self.al.register_callback(self.al.CALLBACK_ILLUMINANCE,
                                              self.cb_illuminance)
                    log.info('Ambient Light initialized')
                except Error as e:
                    log.error('Ambient Light init failed: ' + str(e.description))
                    self.al = None
            elif device_identifier == AmbientLightV2.DEVICE_IDENTIFIER:
                try:
                    self.al_v2 = AmbientLightV2(uid, self.ipcon)
                    self.al_v2.set_configuration(AmbientLightV2.ILLUMINANCE_RANGE_64000LUX,
                                                 AmbientLightV2.INTEGRATION_TIME_200MS)
                    self.al_v2.set_illuminance_callback_period(1000)
                    self.al_v2.register_callback(self.al_v2.CALLBACK_ILLUMINANCE,
                                                 self.cb_illuminance_v2)
                    log.info('Ambient Light 2.0 initialized')
                except Error as e:
                    log.error('Ambient Light 2.0 init failed: ' + str(e.description))
                    self.al_v2 = None
            elif device_identifier == Humidity.DEVICE_IDENTIFIER:
                try:
                    self.hum = Humidity(uid, self.ipcon)
                    self.hum.set_humidity_callback_period(1000)
                    self.hum.register_callback(self.hum.CALLBACK_HUMIDITY,
                                               self.cb_humidity)
                    log.info('Humidity initialized')
                except Error as e:
                    log.error('Humidity init failed: ' + str(e.description))
                    self.hum = None
            elif device_identifier == Barometer.DEVICE_IDENTIFIER:
                try:
                    self.baro = Barometer(uid, self.ipcon)
                    self.baro.set_air_pressure_callback_period(1000)
                    self.baro.register_callback(self.baro.CALLBACK_AIR_PRESSURE,
                                                self.cb_air_pressure)
                    log.info('Barometer initialized')
                except Error as e:
                    log.error('Barometer init failed: ' + str(e.description))
                    self.baro = None

    def cb_connected(self, connected_reason):
        if connected_reason == IPConnection.CONNECT_REASON_AUTO_RECONNECT:
            log.info('Auto Reconnect')

            while True:
                try:
                    self.ipcon.enumerate()
                    break
                except Error as e:
                    log.error('Enumerate Error: ' + str(e.description))
                    time.sleep(1)

if __name__ == "__main__":
    log.info('Weather Station: Start')

    weather_station = WeatherStation()

    if sys.version_info < (3, 0):
        input = raw_input # Compatibility for Python 2.x
    input('Press key to exit\n')

    if weather_station.ipcon != None:
        weather_station.ipcon.disconnect()

    log.info('Weather Station: End')
