import re
import os
import time
import random
import pickle
import logging
import requests

import utils
import config
from exception import SecKillException


path = utils.JdSecKillPath()


class JdSession:
    def __init__(self):
        self.session = requests.session()
        self.headers = config.HEADERS
        self.session.headers = self.headers

    @property
    def cookies(self):
        return self.session.cookies

    @cookies.setter
    def cookies(self, cookies):
        self.session.cookies.update(cookies)


class JdQrcodeLogin(JdSession):

    def __init__(self):
        super(JdQrcodeLogin, self).__init__()
        self.__load_cookies_from_local()
        self.is_login = self.refresh_login()

    def __get_login_page(self):
        """获取PC端登录页面
        理论上可以直接获取二维码，这里模拟正常操作，先调起页面再处理二维码
        """
        url = "https://passport.jd.com/new/login.aspx"
        page = self.session.get(url, headers=self.headers)
        return page

    def __get_login_qrcode(self):
        """获取登录二维码并自动打开
        https://qr.m.jd.com/show?appid=133&size=147&t=1611304511060
        return: boolean
        """
        url = "https://qr.m.jd.com/show"
        payload = {
            "appid": 133,
            "size": 147,
            "t": utils.get_current_json_timestamp()
        }

        r = self.session.get(url=url, params=payload, headers=self.headers)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            logging.error(f"登录二维码获取({r.status_code})：{r.text}")
            return False

        qrcode_name = path("qrcode.png").abs_path_str()
        utils.dumps_bytes_to_file(r, qrcode_name)
        utils.open_file(qrcode_name)
        logging.info(f"登录二维码已生成：{qrcode_name}")
        logging.info(f"登录二维码已弹出，请打开京东 APP 扫码登录!")
        return True

    def __get_qrcode_ticket(self):
        """轮询是否扫码成功回调
        return: None or ticket
        """
        url = "https://qr.m.jd.com/check"
        payload = {
            "callback": f"JQuery{random.randint(1000000, 9999999)}",  # 7位随机数
            "appid": 133,
            "token": self.session.cookies.get("wlfstk_smdl"),
            "_": utils.get_current_json_timestamp()
        }
        # 必填请求头，不写服务器报参数错误
        self.headers["Referer"] = 'https://passport.jd.com/new/login.aspx'

        r = self.session.get(url=url, params=payload, headers=self.headers)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            logging.error(f"二维码登录回调({r.status_code})：{r.text}")
            return
        logging.debug(r.text)
        result = utils.loads_str_to_json(r.text)
        code = result["code"]
        if code != 200:
            msg = result["msg"]
            logging.info(f"二维码登录回调({code})：{msg}")
            return
        ticket = result["ticket"]  # 仅 code 为 200 时，返回 ticket
        logging.debug(f"二维码登录回调({code})：ticket ==> {ticket}")
        return ticket

    def __get_ticket_retry(self):
        """登录二维码有效时间为3分钟
        """
        for i in range(85):
            ticket = self.__get_qrcode_ticket()
            if ticket:
                return ticket
            time.sleep(2)

    def __validate_qrcode_ticket(self, ticket):
        """校验 ticket 是否有效
        return: boolean
        """
        url = 'https://passport.jd.com/uc/qrCodeTicketValidation'
        # 必填请求头，不写服务器报参数错误
        self.headers["Referer"] = 'https://passport.jd.com/uc/login?ltype=logout'
        r = self.session.get(url=url, params={"t": ticket}, headers=self.headers)

        try:
            r.raise_for_status()
        except requests.HTTPError:
            logging.error(f"Ticket 校验({r.status_code})：{r.text}")
            return

        result = r.json()
        if result["returnCode"] != 0:
            logging.info(f"Ticket 校验失败：{result}")
            return
        logging.debug(f"Ticket 校验成功：{result}")
        return True

    def __validate_login_status(self):
        """验证cookies是否有效，通过访问我的订单页面，验证是否已经登录成功
        return: boolean
        """
        url = 'https://order.jd.com/center/list.action'
        payload = {'rid': utils.get_current_json_timestamp()}
        r = self.session.get(url=url, params=payload, allow_redirects=False)

        try:
            r.raise_for_status()
            if r.status_code != requests.codes.OK:
                # 如果登录失败会重定向到登录页面 3xx
                logging.debug(f"当前未登录({r.status_code})")
                return False
        except requests.HTTPError:
            logging.error(f"登录失败({r.status_code})：{r.text}")
            return False
        return True

    def get_nickname(self):
        """获取用户信息
        """
        url = 'https://passport.jd.com/user/petName/getUserInfoForMiniJd.action'
        payload = {
            'callback': f'jQuery{random.randint(1000000, 9999999)}',
            '_': utils.get_current_json_timestamp(),
        }
        self.headers['Referer'] = 'https://order.jd.com/center/list.action'

        r = self.session.get(url=url, params=payload, headers=self.headers)
        result = r.text
        logging.debug(f"UserInfo：{result}")
        nickname = utils.loads_str_to_json(result).get("nickName")
        # imgUrl | lastLoginTime | plusStatus | realName | userLevel | userScoreVO
        return nickname

    def __load_cookies_from_local(self):
        """从本地加载 cookies
        """
        cookies_file = None
        for filename in os.listdir(path.abs_path_str()):
            if filename.endswith(".cookies"):
                cookies_file = f"{path.abs_path_str()}/{filename}"
                break
        if cookies_file is None:
            logging.debug("目前暂无缓存 cookies 文件")
            return
        try:
            logging.debug(f"cookies file ==> {cookies_file}")
            with open(cookies_file, 'rb') as f:
                local_cookies = pickle.load(f)
            self.cookies = local_cookies
        except FileNotFoundError:
            logging.error(f"{cookies_file} not found.")

    def __save_cookies_to_local(self, nickname):
        cookies_file = f"{path.abs_path_str()}/{nickname}.cookies"
        with open(cookies_file, "wb") as f:
            pickle.dump(self.cookies, f)
        logging.info(f"创建并存储 ==> {cookies_file}")

    def login(self):
        """二维码登录流程
        """
        try:
            # 1. 获取登录页面
            self.__get_login_page()
            # 2. 获取登录二维码并下载弹出，供扫码
            self.__get_login_qrcode()
            # 3. 循环检测扫码状态，在二维码有效期内获取 ticket
            ticket = self.__get_ticket_retry()
            # 4. 校验登录
            # 4.1 校验 ticket 信息
            if self.__validate_qrcode_ticket(ticket):
                # 4.2 校验登录状态
                if self.__validate_login_status():
                    logging.info("二维码登录成功")
                    logging.info(f"登录用户：{self.get_nickname()}")
                    # 4.3 保存 cookies
                    self.__save_cookies_to_local(self.get_nickname())
        except SecKillException:
            logging.error("二维码登录失败")

    def refresh_login(self):
        """判断当前是否已经登录
        return: boolean
        """
        if self.__validate_login_status():
            logging.info(f"当前登录用户：{self.get_nickname()}")
            return True
        return False
