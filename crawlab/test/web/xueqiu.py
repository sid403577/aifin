import datetime
import json
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

normalUrl = "https://api.crawlbase.com/?token=gRg5wZGhA4tZby6Ihq_6IQ"


def download_page(url, para=None):
    crawUrl = f"{normalUrl}{urllib.parse.quote(url)}"
    if para:
        response = requests.get(crawUrl, params=para)
    else:
        response = requests.get(crawUrl)
    # response.encoding = response.apparent_encoding
    if response.status_code == 200:
        return response.text
    else:
        print("failed to download the page")


def xueqiu(code: str, type: str):  # 两个参数分别表示开始读取与结束读取的页码

    headers = ['date', 'source', 'link', 'title', 'text', 'code', 'createTime', ]
    # 遍历每一个URL
    total = 0
    pageIndex = 1
    pageSize = 10
    flag = True
    oUser_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.1.1 Safari/605.1.15'
    user_agent = urllib.parse.quote(oUser_agent)
    Cookie = 'Hm_lvt_1db88642e346389874251b5a1eded6e3=1687333713; device_id=e01e4ad350f7731ce697d41fa17a990f; s=bn16jia1w2; xq_a_token=57b2a0b86ca3e943ee1ffc69509952639be342b9; xqat=57b2a0b86ca3e943ee1ffc69509952639be342b9; xq_r_token=59c1392434fb1959820e4323bb26fa31dd012ea4; xq_id_token=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJ1aWQiOi0xLCJpc3MiOiJ1YyIsImV4cCI6MTY5MDMzMTY5OCwiY3RtIjoxNjg3NzQ0MTAwODM4LCJjaWQiOiJkOWQwbjRBWnVwIn0.nRrEcIuOVrMRzBBxKoNmShAZhginw7ld0aRapsbFVzpj73q9cYtDH1Dw0Q87wjaIXF0ZyvrqZJ33-sMcE0Rkc1fVtHOKlCQiLfpuqsZfM--mlaKJqcbtAQmyBrLbsk0x2e8j8if1CkOzssAf7wyqdWsMQhbIXbc0tR5GanjHgvWmYH1GLKQ-QlzIu4shK9rDC3u0DZ2bHBEuAE4C2YhnYX4cdQR4TooUN24g1tlo18zEZCQ9HVXvxm9LhfqyCmynaAvEnsumyaeMJNmEAfeKimNCAFhPbYRlQVZY3VMFwZLJ0y5cx1u5C5tOLIViMpxRZLnHClVPfwX1-f1nh2STrg; u=971687748490780; cookiesu=971687748490780; acw_sc__v2=6498ff8f35c03fe0111df270c15dcadf548046ab; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1687749107'
    cookies = urllib.parse.quote(Cookie)

    while flag:
        url = f'https://xueqiu.com/statuses/stock_timeline.json?symbol_id=S{code}&count={pageSize}&source=%E8%87%AA%E9%80%89%E8%82%A1%E6%96%B0%E9%97%BB&page={pageIndex}'
        print(f"url:{url}")  # 用于检查
        crawUrl = f"{normalUrl}&url={urllib.parse.quote(url)}&cookies={cookies}&user_agent={user_agent}"
        response = requests.get(crawUrl, verify=False, timeout=30)  # 禁止重定向
        print(response.text)
        soup = BeautifulSoup(response.text)
        content = soup.select("body pre")[0].get_text()
        print(content)
        # 读取的是json文件。因此就用json打开啦
        result = json.loads(content)
        # 找到原始页面中数据所在地
        data = result['list']
        if len(data)> 0:
            print(f"获取第{pageIndex}页的数据，大小为{len(data)}")
            storageList: list = []
            for i in range(0, len(data)):

                try:
                    #发布时间
                    created_at = datetime.datetime.timestamp(datetime.datetime.now())
                    if 'created_at' in data[i]:
                        created_at = data[i]['created_at']
                    date = datetime.datetime.fromtimestamp(created_at).strftime('%Y-%m-%d %H:%M:%S')
                    if type == "1":
                        s_time = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S').date()
                        now_time = datetime.datetime.now().date()
                        if s_time < now_time:
                            print(f"当天数据已经处理完成，跳出循环")
                            flag = False
                            break

                    total += 1
                    print(f"开始处理第{total}条数据：{data[i]}")
                    # 数据处理
                    print(f"获取第{total}条数据的link内容：{link}")
                    text = get_text(data[i]['url'])
                    source = data[i]['mediaName']
                    link = data[i]['url']
                    title = data[i]['title']
                    createTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # 写入
                    result_item1 = [date, source, link, title, text, code, createTime]
                    storageList.append(result_item1)

                    print(f"第{total}条数据处理完成")

                except Exception as e:
                    print(
                        f"获取第【{pageIndex}】页的第【{i}】条数据,title:{data[i]['title']},url:{data[i]['url']}时异常，异常信息：{e}")
            # 存入矢量库
            if len(storageList) > 0:
                pass

        if len(data) < pageSize:
            break
        pageIndex += 1

    print(f"处理完成，一共处理{total}条数据")


def get_text(url):
    soup = BeautifulSoup(download_page(url))
    pattern = re.compile("txtinfos")  # 按标签寻找
    all_comments = soup.find_all("div", {'class': pattern})
    if all_comments and len(all_comments) > 0:
        text1 = all_comments[0]
        con = text1.get_text()  # 只提取文字
    else:
        con = soup.get_text()
    return con


if __name__ == "__main__":
    # code = input('请输入股票代码：')
    # Start = input('请输入起始页：')
    # size = input('请输入每页大小：')
    # End = input('请输入结束页：')
    # code = sys.argv[1]  # 股票代码
    # type = sys.argv[2]  # 增量1，全量2
    xueqiu("002624", "1")
    # output_csv(result)
