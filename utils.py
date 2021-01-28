import os
import sys
import time
import json
import config
import shutil
import logging
import requests
import datetime


def dumps_bytes_to_file(resp, file_path):
    """将服务器响应字节流转储到文件
    """
    with open(file_path, 'wb') as f:
        # Iterates over the response data.
        # The chunk size is the number of bytes it should read into memory.
        for chunk in resp.iter_content(chunk_size=1024):
            f.write(chunk)


def loads_str_to_json(text):
    """反序列化，将字符串转化为 json
    """
    begin = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[begin:end])


def open_file(file):
    """不同系统打开文件
    """
    platform = sys.platform
    cmd = None
    if "win" in platform:
        if platform == "darwin":
            cmd = "open"  # for Mac
        else:
            cmd = "start"  # for Windows
    if "linux" in platform:
        if "deepin" in os.uname()[2]:
            cmd = "deepin-image-viewer"  # for deepin
        else:
            cmd = "eog"  # for Linux
    os.system(f"{cmd} {file}")
    time.sleep(0.5)


def get_current_json_timestamp():
    """python的时间戳区别于json，毫秒部分为小数点，需要 *1000 后取整
    """
    return int(time.time() * 1000)


def send_wechat(message, title="抢购结果"):
    """推送信息到微信
    """
    url = f"http://sc.ftqq.com/{config.sckey}.send"
    payload = {"text": title, "desc": message}
    headers = {'User-Agent': config.DEFAULT_USER_AGENT}
    requests.get(url, params=payload, headers=headers)
    logging.info("Send wechat ！")
    logging.info("hhhhhh")


def get_seckill_result_by_log():
    """读取日志，获取抢购结果
    """
    keyword = "抢购成功"
    file_path = JdSecKillPath().log("output.log").abs_path_str()

    with open(file_path, "r+", encoding="utf-8") as f:
        for line in f.readlines():
            if keyword in line:
                return keyword, line.strip()
        return "抢购失败", "日志内未出现「抢购成功」，所以认为抢购失败"


def log_bak():
    """当天运行完成的日志进行备份
    """
    log_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'log')
    log_name = "output.log"

    log_file = os.path.join(log_path, log_name)
    log_file_bak = os.path.join(
        log_path,
        f"{(datetime.datetime.now()).strftime('%y%m%d')}_{log_name}"
    )

    try:
        shutil.copy(log_file, log_file_bak)
        os.remove(log_file)
    except FileNotFoundError:
        print(f"The log backup failed.")
    print("The backup to complete.")


class JdSecKillPath:
    """生成路径的自定义类，根据传入的属性生成不同的路径
    Usage：
        根据属性生成【相对】路径
        >>> JdSecKillPath().log.test.status  # 目录路径 -> object
        /log/test/status
        >>> JdSecKillPath().docs("README.md")  # 文件路径 -> object
        /docs/README.md
        >>> str(JdSecKillPath().log.test)  # 将对象转为 str
        '/log/test'

        根据属性生成【绝对】路径
        >>> JdSecKillPath().log.test.status.abs_path_str() # 目录路径 -> str
        '/Users/lanzy/workspace/PycharmProject/jdSeckill/log/test/status'
        >>> JdSecKillPath().docs("README.md").abs_path_str()  # 文件路径 -> str
        '/Users/lanzy/workspace/PycharmProject/jdSeckill/docs/README.md'
    """
    def __init__(self, path=''):
        self.__path = path

    def __getattr__(self, path):
        return JdSecKillPath(f"{self.__path}/{path}")

    def __str__(self):
        return self.__path

    def __call__(self, name):
        return JdSecKillPath(f"{self.__path}/{name}")

    def abs_path_str(self):
        __abs_path = os.path.abspath(os.path.dirname(__file__))
        return __abs_path + str(self.__str__())

    __repr__ = __str__


if __name__ == '__main__':
    import doctest
    doctest.testmod()
