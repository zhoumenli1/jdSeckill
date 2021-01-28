# -*- coding:utf-8 -*-
import time
import json
import random
import logging
import requests
from datetime import datetime


class Timer:
    def __init__(self):
        self.sleep_interval = 0.5

        # 设置每日抢购时间 2021-01-25 09:59:59.50000
        buy_time = datetime.now().replace(hour=9, minute=59, second=59, microsecond=500000)
        self.buy_time = datetime.strptime(str(buy_time), "%Y-%m-%d %H:%M:%S.%f")

        # 开始抢购时间戳 1609811999500
        self.buy_time_stamp = int(
            time.mktime(self.buy_time.timetuple()) * 1000.0 + self.buy_time.microsecond / 1000
        )

        self.diff_time = self.local_jd_time_diff()

    @staticmethod
    def wait_some_time():
        """随机等待 0.1 - 0.3 秒
        """
        time.sleep(random.randint(100, 300) / 1000)

    @staticmethod
    def jd_time():
        """从京东服务器获取时间毫秒
        """
        url = 'https://a.jd.com//ajax/queryServerData.html'
        ret = requests.get(url).text
        js = json.loads(ret)
        return int(js["serverTime"])

    @staticmethod
    def local_time():
        """获取本地时间毫秒
        """
        return int(round(time.time() * 1000))

    def local_jd_time_diff(self):
        """计算本地与京东服务器时间差
        """
        return self.local_time() - self.jd_time()

    def local_time_greater_than_buy_time(self, minutes=30):
        """计算当前时间与抢购时间的差值，返回布尔值
        默认设置为 30 分钟，当天超过抢购时间30分钟后运行脚本时，
        为了防止无意义的刷接口，直接就停掉程序
        """
        ms = minutes * 60 * 1000
        if self.local_time() >= (self.buy_time_stamp + ms):
            return True
        else:
            return False

    def start(self):
        # 首先进行时间判断，大于抢购时间则直接终止程序
        if self.local_time_greater_than_buy_time():
            logging.info("今天抢购时间已过，明天再来吧～")
            return False

        logging.info(f'正在等待到达设定时间:{self.buy_time}，检测本地时间与京东服务器时间误差为【{self.diff_time}】毫秒')
        while True:
            # 本地时间减去与京东的时间差，能够将时间误差提升到0.1秒附近
            # 具体精度依赖获取京东服务器时间的网络时间损耗
            if self.local_time() - self.diff_time >= self.buy_time_stamp:
                logging.info('时间到达，开始执行……')
                break
            else:
                time.sleep(self.sleep_interval)

