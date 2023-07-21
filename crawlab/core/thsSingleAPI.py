# 获取单只股票的数据
import datetime
import json
import sys

from config.common_config import stockMap
from storage import EsStore,MilvusStore
import requests
from bs4 import BeautifulSoup

marketMap = {
    32: "深圳证券交易所",
    16: "上海证券交易所",
}



def buildMarketdata(stock: str, market: int):
    page = 0
    total = 0
    print(f"========开始获取【{stock}】在【{marketMap[market]}】的数据")
    while True:
        print(f"开始获取第{page + 1}页数据")
        url = f"https://b2b-news.10jqka.com.cn/hxcota/market/stocks/v2/list?stock={stock}&market={market}&type=1&accessKey=74f9abd518ab0970&page={page}&pageSize=50"
        print(f"url:{url}")
        count = 0
        response = None
        while True and count < 3:
            try:
                response = requests.get(url)
                break
            except Exception as e:
                print(f"error,请求url异常,{e}")
                count += 1
        if not response:
            raise Exception("请求url异常")

        if response.status_code == 200:
            response_text = json.loads(response.text)
            if 'data' in response_text:
                length = len(response_text['data'])
                print(f"获取到{length}条数据")
                print("----------------")
                print("\n")
                if length == 0:
                    print(f"原因：{'' if 'msg' not in response_text else response_text['msg']}")
                    break
                storageList: list = []
                for pre_data in response_text['data']:
                    try:
                        total += 1
                        print(f"开始处理第【{total}】条数据")
                        digest = '' if 'digest' not in pre_data else pre_data['digest']
                        uniqueId = '' if 'unique' not in pre_data else pre_data['unique']
                        url = '' if 'url' not in pre_data else pre_data['url']
                        sourceUrl = '' if 'sourceUrl' not in pre_data else pre_data['sourceUrl']
                        detailUrl = '' if 'detailUrl' not in pre_data else pre_data['detailUrl']
                        print(f"digest:{digest}")
                        print(f"unique:{uniqueId}")
                        print(f"url:{url}")
                        print(f"sourceUrl:{sourceUrl}")
                        print(f"detailUrl:{detailUrl}")
                        if len(uniqueId) > 0:
                            id = uniqueId.split("_")[-1]
                            if len(id) > 0:
                                detail_url = f"https://b2b-news.10jqka.com.cn/hxcota/common/info/detail?id={id}&type=1&accessKey=74f9abd518ab0970"
                                print(f"detail_url:{detail_url}")
                                response_detail = requests.get(detail_url)
                                if response_detail.status_code == 200:
                                    response_detail_text = json.loads(response_detail.text)
                                    if 'data' in response_detail_text:
                                        data = response_detail_text['data']
                                        itemId = '' if 'itemId' not in data else data['itemId']  # 资讯id
                                        title = '' if 'title' not in data else data['title']  # 标题
                                        abstract = '' if 'abstract' not in data else data['abstract']  # 摘要
                                        content = '' if 'content' not in data else data['content']  # content
                                        time = '' if 'time' not in data else data['time']  # 创建时间
                                        contentUrl = '' if 'contentUrl' not in data else data['contentUrl']  # 跳转链接
                                        sourceUrls = '' if 'sourceUrls' not in data else data['sourceUrls']  # 源网地址
                                        source = '' if 'source' not in data else data['source']  # 来源
                                        stockInfo = '' if 'stockInfo' not in data else data['stockInfo']  # 相关个股
                                        try:
                                            soup = BeautifulSoup(content, features="html.parser")
                                            content = soup.get_text()
                                        except:
                                            print("解析异常，获取原有内容")

                                        print(f"资讯id-itemId:{itemId}")
                                        print(f"标题-title:{title}")
                                        print(f"摘要-abstract:{abstract}")
                                        print(f"创建时间-time:{time}")
                                        print(f"来源-source:{source}")
                                        print(f"源网地址-sourceUrls:{sourceUrls}")
                                        print(f"跳转链接-contentUrl:{contentUrl}")
                                        print(f"内容-content:{content}")
                                        print(f"相关个股-stockInfo:{stockInfo}")
                                        s_date = time
                                        try:
                                            s_date = datetime.datetime.fromtimestamp(int(time)).strftime(
                                                '%Y-%m-%d %H:%M:%S')
                                        except:
                                            print("发布时间解析异常，")
                                            s_date = time
                                        createTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                        # 写入矢量库
                                        metadata = {"source": "API",
                                                    "uniqueId": uniqueId,
                                                    "code": stock,
                                                    "url": url,
                                                    "date": s_date,
                                                    "type": "资讯",
                                                    "createTime": createTime,
                                                    "abstract": abstract,
                                                    "title": title,
                                                    "text":content}
                                        storageList.append(metadata)


                        print(f"第{total}条数据处理完成")
                        print("\n")
                    except Exception as e:
                        print(
                            f"获取第【{total}】条数据,title:{title},url:{url}时异常，异常信息：{e}")
                # 存入矢量库
                if len(storageList) > 0:
                    # 存入矢量库
                    MilvusStore.storeData(storageList, f"aifin_{stock}", "8.217.52.63:19530")
                    # 存入es库
                    EsStore.storeData(storageList, f"aifin", "8.217.110.233:9200")
                page += 1
                print(f"第{page}页数据内容获取完毕")

            if 'hasNext' in response_text and not response_text['hasNext']:
                print("hasNext==False，跳出循环")
                break

    print(f"========获取【{stock}】在【{marketMap[market]}】的数据完毕，一共获取到【{total}】条数据")


if __name__ == '__main__':
    if len(sys.argv) > 1:
        stock = sys.argv[1]
        if stock.startswith("6"):
            buildMarketdata(stock, 16)
        else:
            buildMarketdata(stock, 32)
    else:
        for stock in stockMap:
            if stock.startswith("6"):
                buildMarketdata(stock, 16)
            else:
                buildMarketdata(stock, 32)
