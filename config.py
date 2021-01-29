"""
存放一些公共配置
"""

# eid, fp参数必须填写,随意填写可能导致订单无法提交等问题
eid = ""
fp = ""

# 支付密码
# 如果你的账户中有可用的京券（注意不是东券）或 在上次购买订单中使用了京豆，
# 那么京东可能会在下单时自动选择京券支付 或 自动勾选京豆支付。
# 此时下单会要求输入六位数字的支付密码。请在下方配置你的支付密码，如 123456 。
# 如果没有上述情况，下方请留空。
payment_pwd = ''

# server 酱推送服务 ==> http://sc.ftqq.com/3.version
sckey = "SCU141085T64a491f70424366cc47ee4215d1725185feb1371e1a3e"

######################################################################################

DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) " \
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 " \
                     "Safari/537.36"

HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;"
              "q=0.9,image/webp,image/apng,*/*;"
              "q=0.8,application/signed-exchange;"
              "v=b3",
              "Connection": "keep-alive"
}

