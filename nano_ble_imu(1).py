# -*- coding: utf-8 -*-
"""
A simple program to read IMU data at 100Hz from the Arduino Nano 33 IOT board.
"""

import asyncio
from multiprocessing import ProcessError
import struct
import sys
from typing import Dict
import pandas as pd
import numpy as np
from importlib_metadata import csv
import keyboard

import bleak
from bleak import BleakClient
from bleak import discover

# These values have been randomly generated - they must match between the Central and Peripheral devices
# Any changes you make here must be suitably made in the Arduino program as well
IMU_UUID = '13012F01-F8C3-4F4A-A8F4-15CD926DA146'


# Class for handling BLE communication with a Nano board for receiving IMU data.
class NanoIMUBLEClient(object):

    def __init__(self, uuid: str, csvout: bool = True) -> None:
        super().__init__()
        self._client = None
        self._device = None
        self._connected = False
        self._running = False
        self._uuid = uuid
        self._found = False
        self._data = {"time": 0, "mils": 0,
                      "ax": 0.0, "ay": 0.0, "az": 0.0,
                      "gx": 0.0, "gy": 0.0, "gz": 0.0}
        self.packetsize = 30
        self.payloadsize = 7
        # if csvout:
        with open("C:/CMC_Project/data.csv", 'w') as csvfile:
            csvfile.write("time,mils,ax,ay,az,gx,gy,gz\n")

        self._csvout = True
        self.newdata = False
        self.printdata = True

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def data(self) -> Dict:
        return self._data

    @property
    def uuid(self) -> str:
        return self._uuid

    @property
    def running(self) -> bool:
        return self._running

    @property
    def device(self):
        return self._device

    async def connect(self) -> None:
        if self._connected:
            return

        # Currently not connected.
        print('Arduino Nano IMU Service')
        print('Looking for Peripheral Device...')
        devices = await discover()
        for d in devices:
            if 'imu1' in d.name:
                self._found = True
                self._device = d
                sys.stdout.write(f'Found Peripheral Device {self._device.address}. ')
                break

        # Connect and do stuff.
        async with BleakClient(d.address) as self._client:
            sys.stdout.write(f'Connected.\n')
            self._connected = True
            # Start getting data.
            await self.start()
            # Run while connected.
            while self._connected:
                if self._running:
                    # Print data.
                    if self.printdata and self.newdata:
                        # self.print_newdata()
                        self.newdata = False
                    await asyncio.sleep(0)

    async def disconnect(self) -> None:
        if self._connected:
            # Stop notification first.
            self._client.stop_notify()
            self._client.disconnect()
            self._connected = False
            self._running = False

    async def start(self) -> None:
        if self._connected:
            # Start notification
            await self._client.start_notify(self._uuid, self.newdata_hndlr)
            self._running = True

    async def stop(self) -> None:
        if self._running:
            # Stop notification
            await self._client.stop_notify(self._uuid)

    def newdata_hndlr(self, sender, data):
        for i in range(self.payloadsize):
            self._data['time'] = struct.unpack('<L', bytes(data[(i * self.packetsize) + 0:(i * self.packetsize) + 4]))[
                -1]
            self._data['mils'] = struct.unpack('<H', bytes(data[(i * self.packetsize) + 4:(i * self.packetsize) + 6]))[
                -1]
            self._data['ax'] = struct.unpack('<f', bytes(data[(i * self.packetsize) + 6:(i * self.packetsize) + 10]))[
                -1]
            self._data['ay'] = struct.unpack('<f', bytes(data[(i * self.packetsize) + 10:(i * self.packetsize) + 14]))[
                -1]
            self._data['az'] = struct.unpack('<f', bytes(data[(i * self.packetsize) + 14:(i * self.packetsize) + 18]))[
                -1]
            self._data['gx'] = struct.unpack('<f', bytes(data[(i * self.packetsize) + 18:(i * self.packetsize) + 22]))[
                -1]
            self._data['gy'] = struct.unpack('<f', bytes(data[(i * self.packetsize) + 22:(i * self.packetsize) + 26]))[
                -1]
            self._data['gz'] = struct.unpack('<f', bytes(data[(i * self.packetsize) + 26:(i * self.packetsize) + 30]))[
                -1]
            self.print_newdata()

    def print_newdata(self) -> None:

        if self._csvout:
            _str = (f"{self.data['time']:3.0f}, " +
                    # f"{self.data['packetnum']:3.0f}, " +
                    f"{self.data['mils']:3.0f}, " +
                    f"{self.data['ax']:+1.3f}, " +
                    f"{self.data['ay']:+1.3f}, " +
                    f"{self.data['az']:+1.3f}, " +
                    f"{self.data['gx']:+3.3f}, " +
                    f"{self.data['gy']:+3.3f}, " +
                    f"{self.data['gz']:+3.3f}\n")
            with open("D:/arm use/nano ble/data.csv", 'a') as csvfile:
                csvfile.write(_str)

        _str = (f"\r Time: {self.data['time']:3.0f} | " +
                # f"Packet Num: {self.data['packetnum']:3.0f} | " +
                f"Mils: {self.data['mils']:3.0f} | " +
                "Accl: " +
                f"{self.data['ax']:+1.3f}, " +
                f"{self.data['ay']:+1.3f}, " +
                f"{self.data['az']:+1.3f} | " +
                "Gyro: " +
                f"{self.data['gx']:+3.3f}, " +
                f"{self.data['gy']:+3.3f}, " +
                f"{self.data['gz']:+3.3f}")
        sys.stdout.write(_str)
        sys.stdout.flush()


async def run():
    # Create a new IMU client.
    imu_client = NanoIMUBLEClient(IMU_UUID, False)
    await imu_client.connect()


if __name__ == "__main__":
    # df = pd.read_csv('data.csv')
    # freq = df.groupby('time').count()['mils'].values
    # print(df)
    # dataformat = np.dtype({'names': ('time', 'mils', 'ax', 'ay', 'az', 'gx', 'gy', 'gz'),
    #                        'formats': ('u4', 'u2', 'f4', 'f4', 'f4', 'f4', 'f4', 'f4')})
    # dat = pd.DataFrame(np.fromfile("E:/log33.txt", dataformat))
    # freq = dat.groupby('time').count()['mils'].values
    # dat.to_csv('D:/arm use/nano ble/sddata.csv')
    # print(freq)
    # First create an object
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        print('\nReceived Keyboard Interrupt')
    finally:
        print('Program finished')
