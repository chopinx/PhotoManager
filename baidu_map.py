import json
import os
import pickle
from datetime import datetime

import exifread
import piexif
import requests
from PIL import Image


class GPS(object):
    def __init__(self, **kwargs):
        self.decimal = kwargs.get("decimal", None)
        if self.decimal:
            self.D, self.M, self.S = self.decimal2coordinate(self.decimal)
        else:
            self.D = kwargs.get("D", 0)
            self.M = kwargs.get("M", 0)
            self.S = kwargs.get("S", 0)
            self.decimal = self.coordinate2decimal(self.D, self.M, self.S)

    def get_float(self):
        return self.lng, self.lat

    def get_rational(self):
        return (int(self.D), 1), (int(self.M), 1), (int(self.S * 100), 100)

    def get_lng_ref(self):
        if self.decimal >= 180 or self.decimal < 0:
            return "E"
        else:
            return "W"

    def get_lat_ref(self):
        if self.decimal >= 180 or self.decimal < 0:
            return "S"
        else:
            return "N"

    @staticmethod
    def coordinate2decimal(D, M, S):
        """
        将角度转换为浮点数
        :param D: 度
        :param M: 分
        :param S: 秒
        :return: float
        """
        value = float(D) + M / 60 + S / 3600
        return value

    @staticmethod
    def decimal2coordinate(value):
        """
        retrun D,M,S
        """
        abs_value = abs(value)
        D = int(abs_value)
        m = (abs_value - D) * 60
        M = int(m)
        S = round((m - M) * 60, 5)
        return D, M, S


def parse_addr(baidu_map_address):
    return baidu_map_address['result']['addressComponent']['country'], baidu_map_address['result']['addressComponent'][
        'province'], baidu_map_address['result']['addressComponent']['city']


def coordinate2rational(D, M, S):
    result = ((D, 1), (M, 1), (int((M + S / 60) * 100), 100))
    return result


def name2gps(name):
    secret_key = 'hCCwOC0sveRHzCbgZ110xyEtZ4w0UZnG'  # 百度地图创应用的秘钥


class Addr(object):
    def __init__(self, json_data):
        self.result = json_data["result"]
        self.lng = GPS(decimal=self.result["location"]["lng"])
        self.lat = GPS(decimal=self.result["location"]["lat"])
        self.format_addr = self.result["formatted_address"]
        self.component = self.result["addressComponent"]
        self.country = self.component["country"]
        self.province = self.component["province"]
        self.city = self.component["city"]
        self.city_level = self.component["city_level"]
        self.district = self.component["district"]
        self.town = self.component["town"]
        self.street = self.component["street"]
        self.direction = self.component["direction"]
        self.distance = self.component["distance"]


class Coordinate(object):
    def __init__(self, json_data):
        self.result = json_data["result"]
        self.lng = GPS(decimal=self.result["location"]["lng"])
        self.lat = GPS(decimal=self.result["location"]["lat"])
        self.precise = self.result["precise"]
        self.confidence = self.result["confidence"]
        self.comprehension = self.result["comprehension"]
        self.level = self.result["level"]


class BaiduMapAPI(object):
    ak = 'hCCwOC0sveRHzCbgZ110xyEtZ4w0UZnG'

    def __init__(self, addr2gps_cache_path, gps2addr_cache_path):
        self.addr2gps_cache_path = addr2gps_cache_path
        self.gps2addr_cache_path = gps2addr_cache_path
        if addr2gps_cache_path and os.path.exists(addr2gps_cache_path):
            with open(addr2gps_cache_path, "rb") as f:
                self.addr2gps_cache = pickle.load(f)
        else:
            self.addr2gps_cache = {}

        if gps2addr_cache_path and os.path.exists(gps2addr_cache_path):
            with open(gps2addr_cache_path, "rb") as f:
                self.gps2addr_cache = pickle.load(f)
        else:
            self.gps2addr_cache = {}

    def dump(self):
        with open(self.addr2gps_cache_path, "wb") as f:
            pickle.dump(self.addr2gps_cache, f)
        with open(self.gps2addr_cache_path, "wb") as f:
            pickle.dump(self.gps2addr_cache, f)

    def addr2gps(self, addr) -> Coordinate:
        result = self.addr2gps_cache.get(addr, None)
        if result is not None:
            return result
        baidu_map_api = "http://api.map.baidu.com/geocoding/v3/?address={0}&output=json&ak={1}&callback=showLocation".format(
            addr, self.ak)
        response = requests.get(baidu_map_api)
        baidu_map_address = json.loads(response.text[27:-1])
        result = Coordinate(baidu_map_address)
        self.addr2gps_cache[addr] = result
        return result

    def gps2addr(self, lng: GPS, lat: GPS) -> Addr:
        key = "%f,%f" % (lng.decimal, lat.decimal)
        result = self.gps2addr_cache.get(key, None)
        if result is not None and len(result.format_addr) > 0:
            return result
        baidu_map_api = "http://api.map.baidu.com/reverse_geocoding/v3/?ak={0}&output=json&coordtype=wgs84ll&location={1},{2}".format(
            self.ak, lat.decimal, lng.decimal)
        response = requests.get(baidu_map_api)
        baidu_map_address = json.loads(response.text)
        result = Addr(baidu_map_address)
        self.gps2addr_cache[key] = result
        return result


if __name__ == '__main__':
    gps = GPS(decimal=113.211)
    print(gps.get_rational())
    gps = GPS(D=113, M=12, S=39.6)
    print(gps.get_rational())
    baidu_api = BaiduMapAPI("data/addr2gps.dat", "data/gps2addr.dat")
    addr = baidu_api.gps2addr(gps, gps)
    gps = baidu_api.addr2gps("北京")
    baidu_api.dump()
    print(gps)
