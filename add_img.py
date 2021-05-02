import os
import shutil
import time

import baidu_map
import img_utils


def load_md5_set(root_dir, formats=["jpg", "png", "jpeg"]):
    all_path = img_utils.all_photo_path(root_dir, formats)
    md5_path_map = {}
    for path in all_path:
        md5_path_map[img_utils.get_md5(path)] = path
    return md5_path_map


def add_img(src, des, formats=["jpg", "png", "jpeg"]):
    des_md5_map = load_md5_set(des, formats)
    print("there are %d photos in %s" % (len(des_md5_map), des))
    src_path_list = img_utils.all_photo_path(src, formats)
    print("there are %d photos in %s" % (len(src_path_list), des))
    cnt = 0
    for path in src_path_list:
        # time.sleep(1)
        cnt += 1
        if path.split(".")[-1].lower() not in formats:
            print(
                "%d/%d(%.1f%%): unknown format, path=%s" % (
                    cnt, len(src_path_list), cnt * 100 / len(src_path_list), path))
            continue
        src_dir, filename = os.path.split(path)
        new_md5 = img_utils.get_md5(path)
        if des_md5_map.get(new_md5, None) is None:
            old_path = des_md5_map.get(new_md5, None)
            try:
                my_image = img_utils.MyImage(old_path)
                lng, lat = my_image.get_gps()
            except Exception as _:
                print(
                    "%d/%d(%.1f%%): no gps, path=%s" % (
                        cnt, len(src_path_list), cnt * 100 / len(src_path_list), old_path))
                continue
            new_path = os.path.join(des, filename)
            shutil.copy(path, new_path)
            print(
                "%d/%d(%.1f%%): cp %s to %s" % (
                    cnt, len(src_path_list), cnt * 100 / len(src_path_list), path, new_path))
        else:
            print("%d/%d(%.1f%%): %s already exists in %s, path=%s" % (
                cnt, len(src_path_list), cnt * 100 / len(src_path_list), path, des, des_md5_map.get(new_md5, None)))


if __name__ == '__main__':
    add_img(src="D:\\OneDrive - alumni.hust.edu.cn\\图片\\归档相册",
            des="C:\\Users\\xiaoq\\Pictures\\iCloud Photos\\Photos")
