import json

import requests
from bs4 import BeautifulSoup



marketMap={
    16: "上海证券交易所",
    32: "深圳证券交易所",
    48: "新同花顺指数",
    104: "申万指数",
    144: "三板市场",
    176: "香港联交所",
    168: "纽约交易所",
    184: "纳斯达克",
}

def buildMarketdata(stock:str,market:int):
    page = 0
    total = 0
    print(f"========开始获取【{stock}】在【{marketMap[market]}】的数据")
    while True:
        print(f"开始获取第{page+1}页数据")
        url = f"https://b2b-news.10jqka.com.cn/hxcota/market/stocks/v2/list?stock={stock}&market={market}&type=1&accessKey=74f9abd518ab0970&page={page}&pageSize=250"
        response = requests.get(url)
        if response.status_code==200:
            response_text = json.loads(response.text)
            if 'data' in response_text:
                length = len(response_text['data'])
                print(f"获取到{length}条数据")
                if length==0:
                    print(f"原因：{'' if 'msg' not in response_text else response_text['msg']}")
                    break
                for pre_data in response_text['data']:
                    print(f"")
                    digest = '' if 'digest' not in pre_data else pre_data['digest']
                    if 'unique' in pre_data:
                        id = pre_data['unique'].split("_")[-1]
                        if len(id)>0:
                            detail_url = f"https://b2b-news.10jqka.com.cn/hxcota/common/info/detail?id={id}&type=1&accessKey=74f9abd518ab0970"
                            response_detail = requests.get(detail_url)
                            if response_detail.status_code==200:
                                response_detail_text = json.loads(response_detail.text)
                                if 'data' in response_detail_text:
                                    data = response_detail_text['data']
                                    source = '' if 'source' not in data else data['source']
                                    title = '' if 'title' not in data else data['title']
                                    content = '' if 'content' not in data else data['content']
                                    rtime = '' if 'rtime' not in data else data['rtime']
                                    contentUrl = '' if 'contentUrl' not in data else data['contentUrl']
                                    digest = digest
                                    try:
                                        soup = BeautifulSoup(content, features="html.parser")
                                        content =soup.get_text()
                                    except:
                                        print("解析异常，获取原有内容")
                                    print(f"title:{title}")
                                    print(f"rtime:{rtime}")
                                    print(f"source:{source}")
                                    print(f"digest:{digest}")
                                    print(f"content:{content}")
                                    print(f"contentUrl:{contentUrl}")
                                    total += 1
                                    print(f"第{total}条数据处理完成")

        page+=1
        print(f"第{page}页数据内容获取完毕")

    print(f"========获取【{stock}】在【{marketMap[market]}】的数据完毕，一共获取到【{total}】条数据")

if __name__ == '__main__':
    for market in marketMap:
        buildMarketdata("300750",market)