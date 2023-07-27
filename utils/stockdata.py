import requests

from crawlab.core.config.common_config import COMPANY_CODES

# 股票、债券榜单表头
EASTMONEY_QUOTE_FIELDS = {
    'f12': '代码',
    'f14': '名称',
    'f3': '涨跌幅',
    'f2': '最新价',
    'f15': '最高',
    'f16': '最低',
    'f17': '今开',
    'f4': '涨跌额',
    'f8': '换手率',
    'f10': '量比',
    'f9': '动态市盈率',
    'f5': '成交量',
    'f6': '成交额',
    'f18': '昨日收盘',
    'f20': '总市值',
    'f21': '流通市值',
    'f13': '市场编号',
    'f124': '更新时间戳',
    'f297': '最新交易日',
}


def gen_eastmoney_code(rawcode: str) -> str:
    '''
    生成东方财富专用的secid

    Parameters
    ----------
    rawcode ： 6 位股票代码
    Parameters
    ----------
    str : 按东方财富格式生成的字符串
    '''
    if rawcode[0] != '6':
        return f'0.{rawcode}'
    return f'1.{rawcode}'


def getPE_Price(code: str):
    # 股票代码
    # 获取股票的一些基本信息(返回 pandas.Series)
    secids = gen_eastmoney_code(code)

    base_url = f"https://push2.eastmoney.com/api/qt/ulist.np/get"
    params = (
        ('OSVersion', '14.3'),
        ('appVersion', '6.3.8'),
        ('fields', 'f12,f14,f3,f2,f15,f16,f17,f4,f8,f10,f9,f5,f6,f18,f20,f21,f13,f124,f297'),
        ('fltt', '2'),
        ('plat', 'Iphone'),
        ('product', 'EFund'),
        ('secids', secids),
        ('serverVersion', '6.3.6'),
        ('version', '6.3.8'),
    )
    # 请求头
    EASTMONEY_REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; Touch; rv:11.0) like Gecko',
        'Accept': '*/*',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
        # 'Referer': 'http://quote.eastmoney.com/center/gridlist.html',
    }
    try:
        response = requests.get(url=base_url, params=params, headers=EASTMONEY_REQUEST_HEADERS,timeout=1).json()
        data = response['data']
        if data and 'diff' in data:
            diff = data['diff']
            if len(diff) > 0:
                return diff[0]['f297'], diff[0]['f2'], diff[0]['f9']
    except Exception as e:
        print(f"实时获取股票价格和市盈率异常，{e}")


def getCodeByName(sname: str):
    for data in COMPANY_CODES:
        if data['name'] == sname:
            return data['code']


def getTopics(content: str):
    return [data['name'] for data in COMPANY_CODES if data['name'] in content]


if __name__ == '__main__':
    result = getPE_Price("300750")
    print(result[0])
    print(result[1])
    print(result[2])

    # print(getTopics("宁德时代1"))
