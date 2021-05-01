import hashlib
import os
from datetime import datetime

import exifread
import piexif
from PIL import Image

import baidu_map


def all_photo_path(root_dir):
    path_list = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            os.path.join(root, file)
            path_list.append(os.path.join(root, file))

    return path_list


def get_md5(file_path):
    m = hashlib.md5()
    with open(file_path, 'rb') as f:
        m.update(f.read())
        md5value = m.hexdigest()
        return md5value


class MyImage(object):
    def __init__(self, path):
        self.path = path
        with open(self.path, "rb") as f:
            self.tags = exifread.process_file(f)
        self.img = Image.open(path)  # 读图
        self.exif_bytes = ""

    def get_gps(self):
        """

        :return:
            lng: GPS
            lat: GPS
        """
        if 'GPS GPSLatitude' in self.tags.keys():
            lng_ref = 1 if self.tags['GPS GPSLongitudeRef'].values == "E" else -1
            lng = baidu_map.GPS(
                D=self.tags['GPS GPSLongitude'].values[0].num * lng_ref / self.tags['GPS GPSLongitude'].values[0].den,
                M=self.tags['GPS GPSLongitude'].values[1].num * lng_ref / self.tags['GPS GPSLongitude'].values[1].den,
                S=self.tags['GPS GPSLongitude'].values[2].num / self.tags['GPS GPSLatitude'].values[
                    2].den * lng_ref)
            lat_ref = 1 if self.tags['GPS GPSLatitudeRef'].values == "N" else -1
            lat = baidu_map.GPS(D=self.tags['GPS GPSLatitude'].values[0].num / self.tags['GPS GPSLatitude'].values[
                                    0].den * lat_ref,
                                M=self.tags['GPS GPSLatitude'].values[1].num / self.tags['GPS GPSLatitude'].values[
                                    1].den * lat_ref,
                                S=self.tags['GPS GPSLatitude'].values[2].num / self.tags['GPS GPSLatitude'].values[
                                    2].den * lat_ref)
            return lng, lat
        else:
            return None, None

    def get_time(self) -> datetime:
        ori_time = self.tags.get('EXIF DateTimeOriginal', self.tags.get("Image DateTime")).values
        date_time = datetime.strptime(ori_time, "%Y:%m:%d %H:%M:%S")
        return date_time

    def get_time_str(self, f="%Y%m%d_%H%M%S"):
        return self.get_time().strftime(f)

    def set_exif(self, date_time=None, loc_lng=None, loc_lat=None):
        """
        datetime=2014:10:04 12:41:38
        geo=(lat=39.12315,lng=115.12231)
        """
        if 'exif' in self.img.info.keys():
            exif_dict = piexif.load(self.img.info['exif'])  # 提取exif信息
        else:
            img = Image.open("photo/IMG_0013.JPEG")  # 读图
            temp_exif_dict = piexif.load(img.info['exif'])  # 提取exif信息
            exif_dict = {"GPS": temp_exif_dict["GPS"], "Exif": {}}

        if isinstance(date_time, datetime):
            exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_time.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_time.strftime("%Y:%m:%d %H:%M:%S")
        if loc_lng and loc_lat:
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitude] = loc_lng.get_rational()
            exif_dict['GPS'][piexif.GPSIFD.GPSLongitudeRef] = loc_lng.get_lng_ref()
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitude] = loc_lat.get_rational()
            exif_dict['GPS'][piexif.GPSIFD.GPSLatitudeRef] = loc_lat.get_lat_ref()

        self.exif_bytes = piexif.dump(exif_dict)

    def save(self, path):
        self.img.save(path, "jpeg", exif=self.exif_bytes)  # 保存


if __name__ == '__main__':
    my_img = MyImage("photo/IMG_0013.JPEG")
    lng, lat = my_img.get_gps()
    print(lng)
    print(lat)

    my_img.set_exif(date_time=datetime.now(), loc_lng=baidu_map.GPS(decimal=113.211),
                    loc_lat=baidu_map.GPS(decimal=-113.211))
    my_img.save("photo/test.jpg")
