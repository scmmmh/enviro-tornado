import asyncio
import json

from asyncio import Event
from bme280 import BME280
from statistics import mean
from tornado.ioloop import PeriodicCallback, IOLoop
from tornado.web import Application, RequestHandler
from tornado.websocket import WebSocketHandler


bme280 = BME280()
temperature = 0
temperature_readings = []
temperature_update = Event()
humidity = 0
humidity_readings = []
humidity_update = Event()


def collect_measurements():
    global temperature, temperature_readings, temperature_update, humidity, humidity_readings, humidity_update
    
    temperature_readings.append(bme280.get_temperature())
    humidity_readings.append(bme280.get_humidity())
    if len(temperature_readings) > 5:
        temperature_readings.pop(0)
    if len(humidity_readings) > 5:
        humidity_readings.pop(0)
    new_temperature = round(mean(temperature_readings), 1)
    new_humidity = round(mean(humidity_readings), 1)
    if new_temperature != temperature:
        temperature = new_temperature
        temperature_update.set()
    if new_humidity != humidity:
        humidity = new_humidity
        humidity_update.set()


class TemperatureHandler(WebSocketHandler):

    def open(self):
        self.write_message(temperature)
        self.running = True
        IOLoop.current().add_callback(self.periodic)

    def close(self):
        self.running = False

    def check_origin(self, origin):
        return True
    
    async def periodic(self):
        while self.running:
            await temperature_update.wait()
            if self.running:
                self.write_message(temperature)
                temperature_update.clear()


class HumidityHandler(WebSocketHandler):

    def open(self):
        self.write_message(humidity)
        self.running = True
        IOLoop.current().add_callback(self.periodic)

    def close(self):
        self.running = False

    def check_origin(self, origin):
        return True
    
    async def periodic(self):
        while self.running:
            await humidity_update.wait()
            if self.running:
                self.write_message(humidity)
                humidity_update.clear()


def make_app():
    return Application([
        ('/temperature', TemperatureHandler),
        ('/humidity', HumidityHandler),
    ])


def main():
    app = make_app()
    app.listen(8200)
    collect_measurements()
    periodic = PeriodicCallback(callback=collect_measurements, callback_time=60000)
    periodic.start()
    IOLoop.current().start()


if __name__ == "__main__":
    main()
