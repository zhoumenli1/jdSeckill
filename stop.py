import os
import logging
import platform

from timer import Timer


def stop():
    """判断时间，当超过抢购时间后，自动停止程序
    """
    timer = Timer()
    system = platform.system()
    if timer.local_time_greater_than_buy_time(2):  # 设置超出抢购时间时长
        logging.info("jdSeckill >>> The process is over !")
        if system == "Windows":
            # os.system("taskkill /F /IM python.exe")  # 旧版
            os.system("taskkill /F /IM py.exe")  # 3.7.3
        else:
            # Mac | Linux
            os.system("ps -ef | grep python | grep -v grep | cut -c 6-11 | xargs kill -15")
    else:
        logging.info("定时任务设置时长应大于此处的抢购时间时长.")


stop()
