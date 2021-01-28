import logger
import config
import utils as u
from seckill import JdSecKill


def main():

    # 1. 初始化
    seckill = JdSecKill()
    # 2. 预约
    seckill.reserve()
    # 3. 抢购
    seckill.seckill_by_proc_pool()
    # 4. 将结果发送到微信
    if config.sckey:
        u.send_wechat(u.get_seckill_result_by_log())
    # 5. 日志存储
    u.log_bak()


if __name__ == '__main__':
    main()

