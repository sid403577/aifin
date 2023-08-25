#eastmoney行业研报

import datetime
import json
import urllib.parse
import time
import requests

from config.common_config import crowBaseUrl
from utils.urlToData import get_text
from storage import EsStore,MilvusStore


def eastmoney(industryCode: str,industryName:str, type: str, startPage=1):  # 两个参数分别表示开始读取与结束读取的页码


    # 遍历每一个URL
    total = 0
    pageIndex = startPage
    pageSize = 10
    flag = True
    count = 0
    endTime = datetime.date.today()-datetime.timedelta(days=1)
    beginTime = endTime
    if type == "2":
        beginTime = endTime - datetime.timedelta(days=2*365)

    analysis_method = {
        "element": "div",
        "attr": {"class": "ctx-content"},
    }

    while flag and count < 5:
        print(f"开始获取第{pageIndex}页数据")
        st = int(round(time.time() * 1000))
        link = f"https://reportapi.eastmoney.com/report/list?industryCode={industryCode}&pageSize={pageSize}&industry=*&rating=*&ratingChange=*&beginTime={beginTime}&endTime={endTime}&pageNo={pageIndex}&fields=&qType=1&orgCode=&rcode=&_={st}"
        print(f"link:{link}")  # 用于检查
        crawUrl = f"{crowBaseUrl}&url={urllib.parse.quote(link)}"
        try:
            response = requests.get(crawUrl, verify=False, timeout=30)  # 禁止重定向
            print(response.text)
        except:
            count += 1
            continue
        content = response.text
        # 读取的是json文件。因此就用json打开啦
        jsonContent = json.loads(content)
        data=[]
        if "data" in jsonContent:
            data=jsonContent['data']

        print(f"获取第{pageIndex}页的数据，大小为{len(data)}")
        storageList: list = []
        for i in range(0, len(data)):
            print("\n---------------------")
            try:
                total += 1
                print(f"开始处理第{total}条数据：{data[i]}")
                url = f"https://data.eastmoney.com/report/zw_industry.jshtml?infocode={data[i]['infoCode']}"
                text=get_text(url,analysis_method)
                text = text.replace("\n\n", "").replace("  ", "")
                abstract = ""
                if text and len(text)>0:
                    abstract = text[0:100]

                # 数据处理
                metadata = {"source": "Web",
                            "uniqueId": data[i]['infoCode'],
                            "code": industryCode,
                            "name": industryName,
                            "url": url,
                            "date": data[i]['publishDate'],
                            "type": "eastmoney-industry-report",
                            "createTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "abstract": abstract,
                            "title": data[i]['title'],
                            "text":text}
                storageList.append(metadata)

                print(f"第{total}条数据处理完成,数据内容：{json.dumps(metadata,ensure_ascii=False)}")
                print("\n")

            except Exception as e:
                print(
                    f"获取第【{pageIndex}】页的第【{i}】条数据,title:{data[i]['title']},url:{data[i]['url']}时异常，异常信息：{e}")

        if len(storageList) > 0:
            pass
            # 存入矢量库
            #MilvusStore.storeData(storageList,f"aifin_industry_{industryCode}","8.217.52.63:19530")
            # 存入es库
            #EsStore.storeData(storageList, f"aifin_industry", "8.217.110.233:9200")

        print(f"第{pageIndex}页数据处理完成")
        print("\n")
        if len(data) < pageSize:
            break
        pageIndex += 1
        count=0

    print(f"处理完成，从{startPage}-{pageIndex}页，一共处理{total}条数据")






if __name__ == "__main__":
    # domain = sys.argv[1]  # 域名
    # code = sys.argv[2]  # 股票代码
    # type = sys.argv[3]  # 增量1，全量2
    # startPage = sys.argv[4]  # 从第几页
    # print(f"参数列表，domain:{domain},code:{code},type:{type},startPage:{startPage}")
    # eastmoney(code, type, int(startPage))
    eastmoney("1046","游戏", "2", 1)