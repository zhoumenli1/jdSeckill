import logger
import config
import utils as u
from seckill import JdSecKill


def main():
    """welcome
    """
    
    # 1. 初始化
    seckill = JdSecKill()

    # 2. 预约 + 抢购
    seckill.seckill_by_proc_pool()

    """
    3. 将结果发送到微信
    成功默认会发消息，这里是抢购完成后再次检查日志，发送最终结果
    根据需求（可以注释掉）
    """
    # if config.sckey:
    #     title, desc = u.get_seckill_result_by_log()
    #     u.send_wechat(title=title, message=desc)

    """
    # 4. 日志存储
    # 每天运行程序结束后，将日志转储为日期格式的文件名称，适合定时任务
    # 根据需求（可以注释掉）
    """
    # u.log_bak()


if __name__ == '__main__':
    main()

