import datetime
import sys

import pyodbc

from config.common_config import stockMap
from storage import MilvusStore, EsStore
from utils.urlToData import download_page


def transEs(security_code:str,page_index:int=1):
    # Set up the SQL Server connection
    server = '36.137.180.195,24857'
    database = 'emdata'
    username = 'emdata'
    password = 'emdata'

    connection_string = f"DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
    conn = pyodbc.connect(connection_string)
    cursor = conn.cursor()

    # 定义每页的大小和页码
    page_size = 100
    page_number = page_index
    # 计算要跳过的记录数量
    skip_count = (page_number - 1) * page_size
    # skip_count = 2
    has_more_results = True
    while has_more_results:
        query = f"""
            SELECT 
            'DB' as source,
            '公告' as type,
            base.INFOCODE as uniqueId,
            an.SECURITYCODE as code,
            ann_text.TEXT_DOWNLOAD_URL as url,
            base.NOTICETITLE as title,
            base.PUBLISHDATE as date,
            base.SOURCENAME as comeName,
            base.PUBLISHTYPE as publish_type
             FROM INFO_AN_BASINFOCOM base
            left join INFO_ANN_TEXT ann_text on ann_text.INFO_CODE =base.INFOCODE 
            left join INFO_AN_RELCODECOM an on an.INFOCODE =base.INFOCODE 
            WHERE  an.SECURITYCODE={security_code} AND  base.PUBLISHDATE>'2020-01-01 00:00:00'
             ORDER BY base.PUBLISHDATE DESC
            OFFSET {skip_count} ROWS FETCH NEXT {page_size} ROWS ONLY
            """
        cursor.execute(query)
        results = cursor.fetchall()  # Retrieve 500 records at a time

        if not results:
            has_more_results = False
            break
        else:
            page_number = page_number+1
            skip_count = (page_number - 1) * page_size
            # if skip_count == 1:
            #     break;
            # skip_count = 1
        storageList: list = []
        for row in results:
            metadata = {
                'source': row.source,
                'code': row.code,
                'uniqueId': f"{row.uniqueId}",
                'type': row.type,
                'url': row.url if row.url is not None else "",
                'title': row.title,
                'date': row.date,
                'createTime': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'comeName': row.comeName,
                'publishType': row.publish_type,
            }

            text = download_page(metadata['url'])
            metadata['text']=text
            metadata['abstract']=text[0:400]
            storageList.append(metadata)

        if len(storageList) > 0:
            # 存入矢量库
            MilvusStore.storeData(storageList, f"aifin_{security_code}", "8.217.52.63:19530")
            # 存入es库
            EsStore.storeData(storageList, f"aifin", "8.217.110.233:9200")

    # Close the connections
    cursor.close()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        stock = sys.argv[1]  # 股票Code
        transEs(stock, 1)
    else:
        for stock in stockMap:
            transEs(stock, 1)