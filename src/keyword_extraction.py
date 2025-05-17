import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import os
import numpy as np

# 读取情感分析结果数据
input_file_path = os.path.join('data', 'processed_comments.csv')
output_file_path = os.path.join('data', 'processed_data', 'keywords_sbert_simplified.csv')

df = pd.read_csv(input_file_path)

# 确保 'cut_content' 列中没有 NaN 值，去除缺失值
df = df.dropna(subset=['cut_content'])
df['cut_content'] = df['cut_content'].fillna('')  # 如果仍有 NaN，填充为空字符串

# 重置索引，确保索引是连续的
df.reset_index(drop=True, inplace=True)

# 加载预训练的 Sentence-BERT 模型
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # 可以使用其他更强的模型，如 'paraphrase-MiniLM-L6-v2'

# 提取关键词
def extract_keywords(texts, top_n=10):
    # 获取文本的 SBERT 向量表示
    text_embeddings = model.encode(texts, convert_to_tensor=True)
    
    # 假设我们将从文本中提取的关键词用简单的词列表来模拟
    words = [word for text in texts for word in text.split()]
    unique_words = list(set(words))  # 去重

    # 对每个词生成 SBERT 向量表示
    word_embeddings = model.encode(unique_words, convert_to_tensor=True)
    
    # 计算文本与所有词语之间的余弦相似度
    cosine_similarities = cosine_similarity(text_embeddings, word_embeddings)
    
    # 对每个文本，找到与其最相关的 top_n 个词
    top_keywords = []
    for idx, sim in enumerate(cosine_similarities):
        sorted_indices = np.argsort(sim)[::-1][:top_n]  # 按相似度排序，取 top_n 个词
        top_keywords_for_text = [(unique_words[i], sim[i]) for i in sorted_indices]
        top_keywords.append(top_keywords_for_text)
    
    return top_keywords

# 提取关键词
keywords = extract_keywords(df['cut_content'], top_n=10)

# 将关键词保存到 CSV 文件
flattened_keywords = []
for i, keyword_list in enumerate(keywords):
    # 选取相似度最高的三个关键词
    top_3_keywords = [keyword for keyword, _ in keyword_list[:3]]  # 只取前三个关键词
    
    # 补齐长度为3，避免某些情况下关键词不足3个导致报错
    while len(top_3_keywords) < 3:
        top_3_keywords.append(None)  # 或者使用 "" 空字符串表示缺失值

    # 获取原始文本和相似度分数
    text = df.iloc[i]['cut_content']
    similarity_score = keyword_list[0][1]

    # 添加为多个列
    flattened_keywords.append([
        text,
        text,
        top_3_keywords[0],  # keyword1
        top_3_keywords[1],  # keyword2
        top_3_keywords[2],  # keyword3
        similarity_score
    ])

# 创建 DataFrame，并指定列名
keywords_df = pd.DataFrame(flattened_keywords, columns=[
    'cut_content', 
    'text', 
    'keyword1', 
    'keyword2', 
    'keyword3', 
    'similarity_score'
])


# 检查输出文件夹是否存在，不存在则创建
if not os.path.exists(os.path.dirname(output_file_path)):
    os.makedirs(os.path.dirname(output_file_path))

# 保存到 CSV 文件
keywords_df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
print(f"关键词提取完成，已保存至：{output_file_path}")
