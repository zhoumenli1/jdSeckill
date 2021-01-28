import time
import random
import logging
from lxml import etree
from concurrent.futures import ProcessPoolExecutor

import utils
import config
from timer import Timer
from login import JdQrcodeLogin
from exception import SecKillException


class JdSecKill(JdQrcodeLogin):

    def __init__(self):
        super(JdSecKill, self).__init__()
        self.timer = Timer()

        # 抢购商品信息
        self.sku_id = 100012043978
        self.seckill_num = 2

    def check_login(self):
        if self.is_login is False:
            logging.info("当前未登录，请先进行登录！")
            self.login()

    def get_sku_title(self):
        """获取商品名称，SKU=Stock Keeping Unit(库存量单位)
        现在已经被引申为产品统一编号的简称，每种产品均对应有唯一的SKU号
        """
        url = f'https://item.jd.com/{self.sku_id}.html'
        r = self.session.get(url=url)
        html = etree.HTML(r.content)
        title = html.xpath('/html/head/title/text()')  # list
        title = title[0]
        logging.info(f"当前抢购商品：{title}")
        return title

    def get_sku_seckill_url(self):
        """获取商品抢购链接
        """
        url = 'https://itemko.jd.com/itemShowBtn'
        payload = {
            'callback': f'jQuery{random.randint(1000000, 9999999)}',
            'skuId': self.sku_id,
            'from': 'pc',
            '_': utils.get_current_json_timestamp()
        }
        self.headers["Host"] = 'itemko.jd.com'
        self.headers["Referer"] = f'https://item.jd.com/{self.sku_id}.html'

        while True:
            r = self.session.get(url=url, params=payload, headers=self.headers)
            result = utils.loads_str_to_json(r.text)
            logging.debug(result)
            if result.get("url"):
                router_url = f"https:{result.get('url')}"
                seckill_url = router_url.replace("divide", "marathon").replace("user_routing", "captcha.html")
                logging.info(f"抢购链接获取成功：{seckill_url}")
                return seckill_url
            else:
                logging.info("抢购链接为空，暂未到达抢购时间...")
                self.timer.wait_some_time()

    def request_seckill_url(self, seckill_url):
        """获取到抢购链接后，通过请求模拟第一次重定向
        """
        url = seckill_url

        self.headers["Host"] = "marathon.jd.com"
        self.headers["Referer"] = f"https://item.jd.com/{self.sku_id}.html"

        # allow_redirects 禁止自动重定向
        r = self.session.get(url=url, headers=self.headers, allow_redirects=False)
        logging.info(f"发起抢购[redirect ==> 1]：{r.url}")

    def request_seckill_checkout_page(self):
        """访问提交订单结算页面，通过请求模拟第二次重定向
        """
        url = 'https://marathon.jd.com/seckill/seckill.action'
        payload = {
            'skuId': self.sku_id,
            'num': self.seckill_num,
            'rid': int(time.time())
        }
        self.headers["Host"] = "marathon.jd.com"
        self.headers["Referer"] = f"https://item.jd.com/{self.sku_id}.html"

        r = self.session.get(url=url, params=payload, headers=self.headers, allow_redirects=False)
        logging.info(f"发起抢购[redirect ==> 2]：{r.url}")

    def __get_seckill_init_info(self):
        """获取提交订单所需的用户信息
        return: dict()
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/init.action'
        data = {
            'sku': self.sku_id,
            'num': self.seckill_num,
            'isModifyAddress': 'false',
        }
        self.headers["Host"] = "marathon.jd.com"

        r = self.session.post(url=url, data=data, headers=self.headers)
        logging.debug(f"获取订单信息链接：{r.url}")

        try:
            result = utils.loads_str_to_json(r.text)
            logging.info("订单信息初始化成功")
            logging.debug(f"订单信息初始化成功 ==> {result}")
        except Exception as e:
            logging.info("订单信息初始化失败")
            logging.debug(f"订单信息初始化失败[{e}] ==> {r.text}")
            raise SecKillException(f" The return is not as expected, need to json.")
        return result

    def __get_seckill_order_data(self):
        """生成提交抢购订单所需的请求体参数
        :return: Dict()
        """
        # 获取用户秒杀初始化信息
        init_info = self.__get_seckill_init_info()
        logging.debug(f"init info ===> {init_info}")
        default_address = init_info["addressList"][0]
        invoice_info = init_info.get("invoiceInfo", {})  # 发票信息，如果没有返回默认为空
        token = init_info["token"]

        data = {
            "num": self.seckill_num,
            "addressId": default_address["id"],
            'yuShou': 'true',
            'isModifyAddress': 'false',
            'name': default_address['name'],
            'provinceId': default_address['provinceId'],
            'cityId': default_address['cityId'],
            'countyId': default_address['countyId'],
            'townId': default_address['townId'],
            'addressDetail': default_address['addressDetail'],
            'mobile': default_address['mobile'],
            'mobileKey': default_address['mobileKey'],
            'email': default_address.get('email', ''),
            'postCode': '',
            'invoiceTitle': invoice_info.get('invoiceTitle', -1),
            'invoiceCompanyName': '',
            'invoiceContent': invoice_info.get('invoiceContentType', 1),
            'invoiceTaxpayerNO': '',
            'invoiceEmail': '',
            'invoicePhone': invoice_info.get('invoicePhone', ''),
            'invoicePhoneKey': invoice_info.get('invoicePhoneKey', ''),
            'invoice': 'true' if invoice_info else 'false',
            'password': config.payment_pwd,
            'codTimeType': 3,
            'paymentType': 4,
            'areaCode': '',
            'overseas': 0,
            'phone': '',
            'eid': config.eid,
            'fp': config.fp,
            'token': token,
            'pru': ''
        }
        return data

    def submit_seckill_order(self):
        """提交抢购（秒杀）订单
        return: boolean 抢购结果 True/False
        """
        url = 'https://marathon.jd.com/seckillnew/orderService/pc/submitOrder.action'
        payload = {'skuId': self.sku_id}
        data = self.__get_seckill_order_data()
        logging.debug(f"data-form：{data}")
        self.headers["Host"] = "marathon.jd.com"
        self.headers["Referer"] = f"https://marathon.jd.com/seckill/seckill.action?" \
                                  f"skuId={self.sku_id}&num={self.seckill_num}&rid={int(time.time())}"

        r = self.session.post(url=url, params=payload, data=data, headers=self.headers)
        logging.info(f"提交订单 ==> {r.url}")

        try:
            result = utils.loads_str_to_json(r.text)
            logging.debug(f"[JSON] 抢购结果 ==> {result}")
        except Exception as e:
            # 返回 HTML 是系统直接判定抢购失败
            logging.info(f"[HTML] 抢购失败，很遗憾，木有抢到...")
            logging.debug(f"[HTML] 抢购失败：{e}")
            return False

        # 返回信息 查看 README.md 内各种返回情况
        if result.get('success'):
            order_id = result.get('orderId')
            total_money = result.get('totalMoney')
            pay_url = f"https{result.get('pcUrl')}"
            logging.info(f"抢购成功，订单号:{order_id}, 总价:{total_money}, 电脑端付款链接:{pay_url}")
            if config.sckey:
                success_message = "抢购成功，订单号:{}, 总价:{}, 电脑端付款链接:{}".format(order_id, total_money, pay_url)
                utils.send_wechat(success_message)
            return True
        else:
            logging.info(f"抢购失败，{result['errorMessage']}[{result['resultCode']}]")
            return False

    def reserve(self):
        """发起预约
        """
        self.check_login()

        url = 'https://yushou.jd.com/youshouinfo.action?'
        payload = {
            'callback': 'fetchJSON',
            'sku': self.sku_id,
            '_': utils.get_current_json_timestamp(),
        }
        self.headers["Referer"] = f"https://item.jd.com/{self.sku_id}.html"

        r = self.session.get(url=url, params=payload, headers=self.headers)

        try:
            result = utils.loads_str_to_json(r.text)
            reserve_url = result.get('url')

            r = self.session.get(url=f"https:{reserve_url}")
            logging.info(f"预约成功：{r.url}")
            logging.info("预约成功，已获得抢购资格 / 您已成功预约过了，无需重复预约")
        except Exception as e:
            raise SecKillException(f"预约失败 ==> {r.text}")

    def seckill(self):
        """发起抢购
        """
        while True:
            # 设置预设抢购时间，两分钟都没抢到，大概率没了呀
            if self.timer.local_time_greater_than_buy_time(minutes=2):
                logging.info("到达预设抢购时长，程序终止！")
                return

            try:
                self.request_seckill_url(self.get_sku_seckill_url())
                logging.debug("Get seckill url over!")

                self.request_seckill_checkout_page()
                logging.debug("Seckill url redirect over!")

                self.submit_seckill_order()
                logging.debug("Submit seckill order over!")

            except Exception as e:
                logging.error(f'抢购发生异常，稍后继续执行！==> {e}')

            self.timer.wait_some_time()

    def seckill_by_proc_pool(self, work_count=1):
        """多进程并发执行
        """
        # 1. 登录检测
        self.check_login()

        # 2. 抢购时间检测
        self.timer.start()

        # 3. 多进程抢购
        with ProcessPoolExecutor(work_count) as pool:
            for i in range(work_count):
                pool.submit(self.seckill)
