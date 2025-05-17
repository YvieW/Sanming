import pandas as pd
import re
import jieba
import nltk
from nltk.corpus import stopwords
import string
import os

# 确保下载了 NLTK 停用词
nltk.download('stopwords')

# 设置路径
input_file_path = os.path.join('data', '1_search_comments_2025-05-15.csv')
output_file_path = os.path.join('data', 'processed_comments.csv')

# 读取原始 CSV 文件
df = pd.read_csv(input_file_path)

# 查看数据框架前几行，了解数据结构
print("数据框架预览:")
print(df.head())

# 保留需要的字段
df = df[['content']]

# 清理评论文本
def clean_text(text):
    if not isinstance(text, str):
        return ""  # 如果不是字符串，返回空字符串
    
    # 处理表情，去掉“[笑哭R]”中的“R”，保留“[笑哭]”
    text = re.sub(r'\[([^\]]*)R\]', r'[\1]', text)
    
    # 删除所有非字母数字字符（保留中文和已经处理过的表情）
    text = re.sub(r'[^\w\s\u4e00-\u9fa5\[\]]', '', text)
    
    # 将文本转换为小写，避免表情内容被转为小写
    text = text.lower()
    
    # 删除多余的空格
    text = ' '.join(text.split())
    
    return text

# 清理所有评论
df['cleaned_content'] = df['content'].apply(clean_text)

# 分词（使用 jieba）
def jieba_cut(text):
    return ' '.join(jieba.cut(text))

# 对清理后的评论进行分词
df['cut_content'] = df['cleaned_content'].apply(jieba_cut)

# 去除停用词
stop_words = set(stopwords.words('chinese'))

def remove_stopwords(text):
    words = text.split()
    filtered_words = [word for word in words if word not in stop_words]
    return ''.join(filtered_words)

df['final_content'] = df['cut_content'].apply(remove_stopwords)

# 保存处理后的数据到新的 CSV 文件
df.to_csv(output_file_path, index=False, encoding='utf-8-sig')

print("文本预处理完成，处理后的数据已保存至:", output_file_path)
