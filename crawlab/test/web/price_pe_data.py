# 导入 efinance 库
import efinance as ef


def getPE_Price(code:str):
    # 股票代码
    # 获取股票的一些基本信息(返回 pandas.Series)
    df= ef.stock.get_latest_quote(code)
    print(df)
    if not df.empty:
        return df.get("最新交易日"),df.get("最新价"), df.get("动态市盈率")

if __name__ == '__main__':
    result = getPE_Price("300750")
    print(result[0])
    print(result[1])
    print(result[2])