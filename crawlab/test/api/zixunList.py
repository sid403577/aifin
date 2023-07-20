#获取资讯列表数据

import json

import requests
from bs4 import BeautifulSoup


def buildMarketdata(scenes: int, beginTime: int=None, endTime: int=None):
    page = 0
    total = 0
    url = f"https://b2b-news.10jqka.com.cn/hxcota/app/limitList?id=2883&accessKey=74f9abd518ab0970&pageSize=100&scenes={scenes}"
    if scenes == 1:
        if not beginTime or not endTime:
            raise Exception("scenes==1时，beginTime和endTime必传")
        url += f"&beginTime={beginTime}&endTime={endTime}"
    while True:
        url += f"&page={page}"
        print(f"开始获取第{page + 1}页数据")
        print(f"url:{url}")
        response = requests.get(url)
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
                for pre_data in response_text['data']:
                    total += 1
                    print(f"开始处理第【{total}】条数据")
                    itemId = '' if 'itemId' not in pre_data else pre_data['itemId']  # 资讯id,可通过该ID获取单篇资讯的详细内容。
                    time = '' if 'time' not in pre_data else pre_data['time']  # 发布时间
                    title = '' if 'title' not in pre_data else pre_data['title']  # 标题
                    isAbstract = '' if 'isAbstract' not in pre_data else pre_data['isAbstract']  # 摘要
                    source = '' if 'source' not in pre_data else pre_data['source']  # 来源
                    copyright = '' if 'copyright' not in pre_data else pre_data[
                        'copyright']  # 版权类型:0:无版权；1：有版权；为1时可使用同花顺底层页；为0时建议跳转源网地址。
                    contentUrl = '' if 'contentUrl' not in pre_data else pre_data['contentUrl']  # 同花顺资讯链接
                    detailUrl = '' if 'detailUrl' not in pre_data else pre_data['detailUrl']  # 同花顺资讯链接
                    sourceUrls = '' if 'sourceUrls' not in pre_data else pre_data['sourceUrls']  # 源网链接
                    isImport = '' if 'isImport' not in pre_data else pre_data['isImport']  # 重要性:0,1,2,3，数值越大越重要
                    nature = '' if 'nature' not in pre_data else pre_data['nature']  # 正负面,0:无；1:正面；2:负面；
                    print(f"itemId:{itemId}")
                    print(f"time:{time}")
                    print(f"title:{title}")
                    print(f"isAbstract:{isAbstract}")
                    print(f"source:{source}")
                    print(f"copyright:{copyright}")
                    print(f"contentUrl:{contentUrl}")
                    print(f"detailUrl:{detailUrl}")
                    print(f"sourceUrls:{sourceUrls}")
                    print(f"isImport:{isImport}")
                    if itemId:
                        detail_url = f"https://b2b-news.10jqka.com.cn/hxcota/common/info/detail?id={itemId}&type=1&accessKey=74f9abd518ab0970"
                        print(f"detail_url:{detail_url}")
                        response_detail = requests.get(detail_url)
                        if response_detail.status_code == 200:
                            response_detail_text = json.loads(response_detail.text)
                            if 'data' in response_detail_text:
                                data = response_detail_text['data']
                                itemId = '' if 'itemId' not in data else data['itemId']#资讯id
                                title = '' if 'title' not in data else data['title']#标题
                                abstract = '' if 'abstract' not in data else data['abstract']#摘要
                                content = '' if 'content' not in data else data['content']#内容
                                time = '' if 'time' not in data else data['time']#创建时间
                                contentUrl = '' if 'contentUrl' not in data else data['contentUrl']#跳转链接
                                sourceUrls = '' if 'sourceUrls' not in data else data['sourceUrls']#源网地址
                                source = '' if 'source' not in data else data['source']#来源
                                stockInfo = '' if 'stockInfo' not in data else data['stockInfo']#相关个股
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
                    print(f"第{total}条数据处理完成")
                    print("\n")
            if not response_text['hasNext']:
                print("hasNext==False，跳出循环")
                break

        page += 1
        print(f"第{page}页数据内容获取完毕")

    print(f"========获取资讯列表数据完毕，一共获取到【{total}】条数据")


if __name__ == '__main__':
    buildMarketdata(0)
