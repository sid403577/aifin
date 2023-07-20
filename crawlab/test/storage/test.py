# from pymilvus import connections, Collection
#
# connections.connect("default", host="8.217.52.63", port="19530")
# collection = Collection("aifin_600737")
# collection.delete('source =="Web"')

from milvus import Milvus

# 创建 Milvus 客户端
milvus = Milvus()

# 连接到 Milvus 服务器
milvus.connect(host='localhost', port='19530')

# 定义集合名称和字段名称
collection_name = 'aifin_600737'
field_name = 'source'
field_value = 'core'

# 查询满足条件的向量ID
query_vector = [field_value]  # 将字段值转为向量，根据具体情况进行转换
results = milvus.search(collection_name, query_vector, field_name, top_k=100000)  # 设置合适的 top_k 值

# 提取向量ID
vector_ids = [result.id for result in results[0]]

# 使用向量ID删除向量
status = milvus.delete_entity_by_id(collection_name, vector_ids)

# 检查删除操作的状态
if status.OK():
    print('删除成功')
else:
    print('删除失败')

# 断开与 Milvus 服务器的连接
milvus.disconnect()