


def storeData(docList:list,collection_name:str='aifin_stock',milvusFlag:bool=True):

    import pymongo
    for doc in docList:
        doc.update({'milvusFlag': milvusFlag})

    count = 0
    obj = None
    while True and count < 3:
        try:
            conn = pymongo.MongoClient('mongodb://root:QAZwsx123@36.138.93.247:31966')
            database = conn['milvus_data']
            collection = database[collection_name]
            obj = collection.insert_many(docList)
            break
        except Exception as e:
            count += 1
            print(f"error,写入mongodb库异常 {count}次,{e}")
    if not obj:
        raise Exception(f"写入mongodb库异常{count}次")
    print(f"写入mongodb【{collection_name}】库over")

if __name__ == '__main__':
    metadata = [{"source": "Web",
                "uniqueId": 'A111',
                "code": '123',
                "name": 'stockName',
                "url": 'url',
                "date": '2023-09-09',
                "type": "eastmoney-stock-report",
                "createTime": '2022-09-08',
                "abstract": 'abstract',
                "title": '你好',
                "mediaName": '中国',
                "text": 'text'}]
    storeData(metadata)



