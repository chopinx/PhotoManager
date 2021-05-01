# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
import fractions
import hashlib
import json
import os
import random
import re
import shutil
from datetime import datetime
from shutil import copyfile

import exifread
import piexif
import pyexiv2 as pyexiv2
import requests
from PIL import Image

import baidu_map
import img_utils

reg = re.compile(r'^(?P<year>\d\d\d\d)\.(?P<m>\d+)\.(?P<d>\d+)\-(?P<addr>[\S\s]+)')


class Time(object):
    def __init__(self):
        self.h = 8
        self.m = 0
        self.s = 0

    def add(self):
        self.s += 1
        if self.s >= 60:
            self.m += 1
            self.s -= 60
        if self.m >= 60:
            self.h += 1
            self.m -= 60
        self.h %= 24


addr_map = {"户外运动": "湖北省华中科技大学",
            "河南楂岈山": "河南楂岈山",
            "22ers新年运动会": "孝感学院",
            "本科毕业照": "湖北省武汉市华中科技大学",
            "华农行": "湖北省华中农业大学",
            "澴河": "孝感市孝南区澴河",
            "花": "孝感市",
            "毕业照": "湖北省华中科技大学",
            "钟祥·大洪": "钟祥·大洪",
            "桃花": "孝感市杨店",
            "港澳": "珠海",
            "襄樊": "襄樊",
            "河南灵山": "河南灵山",
            "华中科技大学": "湖北省武汉市华中科技大学",
            "清凉寨": "清凉寨",
            "恩施风光": "恩施风景区",
            "北京": "北京天安门",
            "鄂州梁子湖": "鄂州梁子湖",
            "钟祥·大洪山": "钟祥·大洪山",
            "武汉植物园": "武汉植物园",
            "风景": "孝感市",
            "散步": "孝感市",
            "老家": "孝感市农四村",
            "木兰天池": "木兰天池",
            "家里": "孝感市孝南区彭家湾",
            "黄山": "黄山风景区",
            "西安·延": "西安",
            "木兰草原": "木兰草原",
            "桂林": "桂林市",
            "拍摄作品": "孝感市董永公园",
            "西安·延安": "西安·延安",
            "公园": "孝感市槐荫公园",
            "234寝室": "湖北省武汉市华中科技大学韵苑学生公寓",
            "槐荫公园": "孝感市槐荫公园",
            "泰山·黄河": "泰山·黄河",
            "湖南岳阳": "湖南岳阳",
            "孝感学院": "孝感学院",
            "孝感学院菊花": "孝感学院",
            "毕业季": "湖北省华中科技大学",
            "华科234": "湖北省华中科技大学韵苑学生公寓",
            "黄冈": "湖北黄冈",
            "黄山（毕业旅行）": "黄山",
            "山东": "山东",
            "河南嵖岈山": "河南嵖岈山",
            "湖南": "湖南长沙",
            "董永公园": "董永公园",
            "后湖和董永": "孝感市后湖公园",
            "杨店": "孝感市杨店",
            "武大樱花": "湖北省武汉大学",
            "恩施": "恩施风景区",
            "日常": "孝感市",
            "广场": "孝感市人民广场",
            "泰山·黄": "泰山风景区",
            "大姐": "孝感市",
            "蜈支洲岛": "蜈支洲岛",
            "摄影": "孝感市",
            "咸宁": "咸宁",
            "罗曼之约": "孝感市罗曼之约国际婚纱会馆",
            "亲人": "孝感市孝南区",
            "户外运动": "湖北省华中科技大学",
            "华科电信15届毕业照": "湖北省华中科技大学"}


def split_by_time(list_path, offset, limit, has_time_dir, no_time_dir):
    not_img_dir = os.path.join("data", "not_img")
    if not os.path.exists(not_img_dir):
        os.makedirs(not_img_dir)
    if os.path.exists(has_time_dir):
        shutil.rmtree(has_time_dir)
    if os.path.exists(no_time_dir):
        shutil.rmtree(no_time_dir)
    with open(list_path, "r") as f:
        text = f.read()
    path_list = text.split("\n")
    path_list = path_list[offset:]
    if len(path_list) > limit:
        path_list = path_list[:limit]
    md5_dup, has_time, no_time, has_gps, no_gps, new_time, new_gps, not_img, all_deal, curr_cnt = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    baidu_api = baidu_map.BaiduMapAPI("data/addr2gps.dat", "data/gps2addr.dat")
    md5_set = set()
    my_time = Time()
    result_text = []
    for path in path_list:
        new_md5 = img_utils.get_md5(path)
        curr_cnt += 1
        if new_md5 in md5_set:
            md5_dup += 1
            continue
        md5_set.add(new_md5)
        my_dir, filename = os.path.split(path)
        sub_dir_list = my_dir.split("\\")
        sub_dir_list.reverse()
        addr_str = None
        for sub_dir in sub_dir_list:
            matched = reg.match(sub_dir)
            if matched:
                items_dict = matched.groupdict()
                year, m, d, addr_str = int(items_dict["year"]), int(items_dict['m']), int(items_dict['d']), items_dict[
                    'addr']
                addr_str = addr_map.get(addr_str, None)
                if addr_str is not None and len(addr_str) > 0:
                    break
        if addr_str is not None and len(addr_str) > 0:
            format_addr = addr_str
        else:
            format_addr = sub_dir_list[0]
        print(addr_str)
        new_coordinate = None
        my_image = None
        new_datetime = None
        try:
            my_image = img_utils.MyImage(path)
            lng, lat = my_image.get_gps()
            addr = baidu_api.gps2addr(lng, lat)
            format_addr = addr.format_addr
            has_gps += 1
            if has_gps % 10 == 0:
                baidu_api.dump()
        except Exception as e:
            if my_image is None:
                not_img += 1
                shutil.copy(path, os.path.join(not_img_dir, filename))
                continue
            no_gps += 1
            print(e)
            if addr_str is not None:
                new_gps += 1
                new_coordinate = baidu_api.addr2gps(addr_str)
                addr = baidu_api.gps2addr(new_coordinate.lng, new_coordinate.lat)
                format_addr = addr.format_addr
        datetime_str = "notime"
        try:
            datetime_str = my_image.get_time_str()
            new_dir = os.path.join(has_time_dir, datetime_str[:6])
            new_path = os.path.join(new_dir, datetime_str + "_" + format_addr + "." + filename.split(".")[-1])
            has_time += 1
        except Exception as e:
            no_time += 1
            new_dir = os.path.join(no_time_dir, datetime_str[:6])
            new_path = os.path.join(new_dir, filename)
            if addr_str is not None:
                new_time += 1
                new_datetime = datetime.now().replace(year=year, month=m, day=d, hour=my_time.h,
                                                      minute=my_time.m, second=my_time.s)
                datetime_str = new_datetime.strftime("%Y%m%d_%H%M%S")
                my_time.add()
                new_dir = os.path.join(no_time_dir, datetime_str[:6])
                new_path = os.path.join(new_dir, datetime_str + "_" + format_addr + "." + filename.split(".")[-1])
            print(e)
        all_deal += 1
        new_dir, new_filename = os.path.split(new_path)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        index = 0
        while os.path.exists(new_path):
            index += 1
            new_path = os.path.join(new_dir,
                                    new_filename.split(".")[0] + "_%d" % index + "." + new_filename.split(".")[
                                        -1])
        if addr_str is not None and (new_coordinate is not None or new_datetime is not None):
            if new_coordinate is not None:
                lng, lat = new_coordinate.lng, new_coordinate.lat
            else:
                lng, lat = None, None
            my_image.set_exif(new_datetime, lng, lat)
            my_image.save(new_path)
        else:
            shutil.copy(path, new_path)
        result_text.append(" ".join([path, new_path]))
        print(
            "%d(deal)+%d(dup)+%d(not_img)=%d(curr_cnt), "
            "%d(has_t)+%d(no_t)=%d(all_deal), "
            "%d(has_g)+%d(no_g)=%d(all_deal), "
            "%d(new_t), %d(new_g)" % (
                all_deal, md5_dup, not_img, curr_cnt,
                has_time, no_time, all_deal,
                has_gps, no_gps, all_deal,
                new_time, new_gps))
        print("%d/%d, %.1f%%" % (curr_cnt, len(path_list), curr_cnt * 100 / len(path_list)))
        assert all_deal + md5_dup + not_img == curr_cnt and has_time + no_time == all_deal and has_gps + no_gps == all_deal
    with open("result.txt", "w") as f:
        f.write("\n".join(result_text))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    root_dir = "photo"
    path_list = img_utils.all_photo_path(root_dir)
    list_path = "%s_list.txt" % root_dir
    with open(list_path, "w") as f:
        f.write("\n".join(path_list))
    offset, limit = 0, 1000000
    split_by_time(list_path, offset, limit, "out/has_time", "out/no_time")
    # set_gps("photo/DSC01625.jpg", "西安·延安")
    # addr = read_gps("photo/gps.jpg")
    # name2gps("西安")

    # path_list = all_photo("photo")
    # print(len(all_photo("photo")))
    # print(len(all_photo("out/has_time")))
    # print(len(all_photo("out/no_time")))
    # print("all_cnt", len(path_list))
    # text = []
    # datetime_set = {}
    # has_time_cnt, no_time_cnt, deal_cnt = 0, 0, 0
    # for path in path_list:
    #     print(path)
    #     my_dir, filename = os.path.split(path)
    #     last_dir = my_dir.split("\\")[-1]
    #     with open(path, "rb") as f:
    #         try:
    #             tags = exifread.process_file(f)
    #             # if len(tags) == 0:
    #             #     continue
    #             # has_gps = False
    #             # for key in tags.keys():
    #             #     if key.find("GPS") >= 0:
    #             #         has_gps = True
    #             keys_set = set(tags.keys())
    #             ori_time = tags.get('EXIF DateTimeOriginal', tags.get("Image DateTime")).values
    #             date_time = datetime.strptime(ori_time, "%Y:%m:%d %H:%M:%S")
    #             datetime_str = date_time.strftime("%Y%m%d_%H%M%S")
    #             index = 0
    #             new_datetime_str = datetime_str + "_%d" % index
    #             while new_datetime_str in datetime_set.keys():
    #                 index += 1
    #                 new_datetime_str = datetime_str + "_%d" % index
    #             datetime_set[new_datetime_str] = path
    #             if index >= 1:
    #                 md5_set = set()
    #                 for i in range(index + 1):
    #                     new_datetime_str = datetime_str + "_%d" % i
    #                     old_path = datetime_set[new_datetime_str]
    #                     md5_set.add(get_md5(old_path))
    #                 if len(md5_set) > 1:
    #                     for i in range(index + 1):
    #                         new_datetime_str = datetime_str + "_%d" % i
    #                         old_path = datetime_set[new_datetime_str]
    #                         new_dir = os.path.join("out", "has_time_dup")
    #                         if not os.path.exists(new_dir):
    #                             os.makedirs(new_dir)
    #                         new_path = os.path.join(new_dir, new_datetime_str + "." + filename.split(".")[-1])
    #                         shutil.copy(old_path, new_path)
    #
    #                     has_time_cnt += 1
    #             # if has_gps:
    #             #     x, y = gps_str2float(tags['GPS GPSLatitude'].values), gps_str2float(tags["GPS GPSLongitude"].values)
    #             # baidu_map_address = find_address_from_GPS(x, y)
    #             # country, province, city = parse_addr(baidu_map_address)
    #             # print(len(text), country, province, city)
    #             # photo = {"path": path, "map_addr": baidu_map_address}
    #             # text.append(json.dumps(photo))
    #         except Exception as e:
    #             # new_dir = os.path.join("out", "no_time", last_dir)
    #             # if not os.path.exists(new_dir):
    #             #     os.makedirs(new_dir)
    #             # shutil.copy(path, os.path.join(new_dir, filename))
    #             # no_time_cnt += 1
    #             print(e)
    #             continue
    #         finally:
    #             deal_cnt += 1
    #             print("%d/%d, has:%d, no:%d" % (deal_cnt, len(path_list), has_time_cnt, no_time_cnt))
    # with open("addr_data.txt", "w") as f:
    #     f.write("\n".join(text))
