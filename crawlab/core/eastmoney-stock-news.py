###################### 获取数据 ###############################################

import datetime
import json
import re
import sys
import time
import urllib.parse

import requests

from config.common_config import crowBaseUrl
from utils.urlToData import get_text
from storage import MongoDbStore,MilvusStore




htmlcontent = {
	"eastmoney-stock-news": {
        "domainurl": "https://search-api-web.eastmoney.com/search/jsonp?cb=jQuery35107761762966427765_1687662386467&_=$st",
        "parse_param": {
            "key": "param",
            "value": '{"uid": "4529014368817886", "keyword": "$code", "type": ["cmsArticleWebOld"], "client": "web", "clientType": "web", "clientVersion": "curr", "param": {"cmsArticleWebOld": {"searchScope": "default", "sort": "time", "pageIndex": $pageIndex, "pageSize": $pageSize, "preTag": "<em>", "postTag": "</em>"}}}',
        },
        "result_re": 'jQuery35107761762966427765_1687662386467\((.*)\)',
        "data": ['result', 'cmsArticleWebOld'],
        "text_re": {
            "element": "div",
            #"attr": {"class": "article"},
            "attr": {"class": "txtinfos"},
        }
    }
}

def eastmoney(code: str,stockName:str, type: str, startPage=1):  # 两个参数分别表示开始读取与结束读取的页码
    domain = "eastmoney-stock-news"
    param_content = htmlcontent[domain]
    if not param_content:
        print(f"该域名数据无法获取，domain:{domain}")
        return

    # 遍历每一个URL
    total = 0
    pageIndex = startPage
    pageSize = 10
    flag = True
    count = 0
    while flag and count < 5:
        print(f"开始获取第{pageIndex}页数据")
        domainurl: str = param_content['domainurl']
        st=int(round(time.time() * 1000))
        domainurl = domainurl.replace("$code", code).replace("$pageIndex", str(pageIndex)).replace("$pageSize",
                                                                                                   str(pageSize)).replace("$st",str(st))
        parse_param = param_content['parse_param']
        link = f"{domainurl}"
        if parse_param:
            key = parse_param['key']
            value: str = parse_param['value']
            value = value.replace("$code", code).replace("$pageIndex", str(pageIndex)).replace("$pageSize",
                                                                                               str(pageSize))
            link = link + "&" + key + "=" + urllib.parse.quote(value)

        print(f"link:{link}")  # 用于检查
        crawUrl = f"{crowBaseUrl}&url={urllib.parse.quote(link)}"
        try:
            response = requests.get(crawUrl, verify=False, timeout=30)  # 禁止重定向
            print(response.text)
        except:
            count += 1
            continue
        content = response.text
        if 'result_re' in param_content:
            content = re.findall(param_content['result_re'], response.text)[0]
        # 读取的是json文件。因此就用json打开啦
        data = json.loads(content)
        # 找到原始页面中数据所在地
        for pre in param_content['data']:
            data = data[pre]

        print(f"获取第{pageIndex}页的数据，大小为{len(data)}")
        storageList: list = []
        for i in range(0, len(data)):
            print("\n---------------------")
            try:
                date = data[i]['date']
                if type == "1":
                    s_date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
                    Yesterday = datetime.date.today() - datetime.timedelta(days=1)
                    if s_date < Yesterday:
                        print(f"昨天的数据已经处理完成，跳出循环")
                        flag = False
                        break

                total += 1
                print(f"开始处理第{total}条数据：{data[i]}")
                # 数据处理
                url = data[i]['url']
                abstract = data[i]['content']
                crawUrl = f"{crowBaseUrl}&url={urllib.parse.quote(url)}"
                text = get_text(crawUrl, param_content['text_re'])
                title:str = data[i]['title']
                if abstract:
                    abstract = abstract.replace('</em>', '').replace('<em>', '').strip()
                if text:
                    text = text.replace('</em>', '').replace('<em>', '').strip()
                else:
                    text = abstract
                if title:
                    title = title.replace('</em>', '').replace('<em>', '').strip()
                metadata = {"source": "Web",
                            "uniqueId": data[i]['code'],
                            "code": code,
                            "name": stockName,
                            "url": url,
                            "date": date,
                            "type": domain,
                            "createTime": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "abstract": abstract,
                            "title": title,
                            "mediaName": data[i]['mediaName'],
                            "text": text}
                storageList.append(metadata)

                print(f"第{total}条数据处理完成,数据内容：{json.dumps(metadata,ensure_ascii=False)}")
                print("\n")

            except Exception as e:
                print(
                    f"获取第【{pageIndex}】页的第【{i}】条数据,title:{data[i]['title']},url:{data[i]['url']}时异常，异常信息：{e}")

        if len(storageList) > 0:
            # 存入矢量库
            milvusFlag = True
            try:
                MilvusStore.storeData(storageList, f"aifin_stock_{code}", "8.217.52.63:19530")
            except:
                print(f"第{pageIndex}页的数据，大小为{len(data)} 存入矢量库异常")
                milvusFlag = False
            # 存入mongoDB库
            MongoDbStore.storeData(storageList, f"aifin_stock", milvusFlag)

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
    # eastmoney(domain, code, type, int(startPage))
    eastmoney("300750","宁德时代", "2", 1)
