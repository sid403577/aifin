# 导入 efinance 库
import efinance as ef

from crawlab.core.config.common_config import COMPANY_CODES


def getPE_Price(code: str):
    # 股票代码
    # 获取股票的一些基本信息(返回 pandas.Series)
    df = ef.stock.get_latest_quote(code)
    if not df.empty:
        return df.get("最新交易日")[0], df.get("最新价")[0], df.get("动态市盈率")[0]

def getCodeByName(sname:str):
    for data in COMPANY_CODES:
        if data['name']==sname:
            return data['code']

def getTopics(content:str):
    return [data['name'] for data in COMPANY_CODES if data['name'] in content]

if __name__ == '__main__':
    # result = getPE_Price("300750")
    # print(result[0])
    # print(result[1])
    # print(result[2])

    print(getTopics("宁德时代1"))
