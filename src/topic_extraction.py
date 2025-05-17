import pandas as pd
import nltk
import gensim
from gensim import corpora
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import jieba

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体（SimHei）
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题

# 确保下载了 NLTK 停用词（虽然我们不使用默认的英文停用词，但可以保留下载部分）
nltk.download('stopwords')

# 设置路径
input_file_path = os.path.join('data', 'processed_comments.csv')
output_file_path = os.path.join('data', 'topic_extracted_comments.csv')
topic_word_freq_file_path = os.path.join('data', 'topic_word_freq.csv')  # 新增保存主题词频的CSV文件路径

# 停用词：使用自定义的多个中文停用词表（可以根据需要更新停用词列表）
stop_words = set()

# 有多个停用词表，依次读取
stopword_files = [
    "data/stopwords-master/cn_stopwords.txt", 
    "data/stopwords-master/hit_stopwords.txt",
    "data/stopwords-master/baidu_stopwords.txt",
    "data/stopwords-master/scu_stopwords.txt", 
    "data/THUOCL-master/THUOCL_medical.txt",
    "data/THUOCL-master/THUOCL_law.txt",
    "data/THUOCL-master/THUOCL_IT.txt", 
    "data/THUOCL-master/THUOCL_diming.txt",
    "data/THUOCL-master/THUOCL_caijing.txt",
    "data/THUOCL-master/THUOCL_chengyu.txt"
]

# 读取所有停用词文件并将它们合并到一个集合中
for stopword_file in stopword_files:
    with open(stopword_file, "r", encoding="utf-8") as f:
        stop_words.update(f.read().splitlines())

# 查看停用词数量，确保读取正确
print(f"共读取了 {len(stop_words)} 个停用词。")

# 文本预处理：分词并去除停用词
def preprocess_text(text):
    if not isinstance(text, str):
        return []  # 如果不是字符串，返回空列表
    # 分词
    words = jieba.lcut(text)
    # 去除停用词
    filtered_words = [word for word in words if word not in stop_words and word.strip()]
    return filtered_words

def main():
    # 读取处理后的 CSV 文件
    df = pd.read_csv(input_file_path)

    # 查看数据框架前几行，了解数据结构
    print("数据框架预览:")
    print(df.head())

    # 确保 'final_content' 列存在
    if 'final_content' not in df.columns:
        raise ValueError("数据框中不存在 'final_content' 列，请检查输入文件的列名。")

    # 对处理后的评论进行分词和停用词去除
    df['processed_content'] = df['final_content'].apply(preprocess_text)

    # 创建字典和语料库
    dictionary = corpora.Dictionary(df['processed_content'])
    corpus = [dictionary.doc2bow(text) for text in df['processed_content']]

    # 使用 LDA 模型进行主题建模
    lda_model = gensim.models.LdaMulticore(corpus, num_topics=4, id2word=dictionary, passes=20, workers=4)

    # 显示每个主题的词汇
    for idx, topic in lda_model.print_topics(-1):
        print(f"主题 #{idx}: {topic}")

    # 获取每个评论的主题分布，并选择最可能的主题
    def get_dominant_topic(text):
        bow = dictionary.doc2bow(text)
        topic_distribution = lda_model[bow]
        # 按概率降序排列，获取最可能的主题
        dominant_topic = sorted(topic_distribution, key=lambda x: x[1], reverse=True)[0][0]
        return dominant_topic

    # 将主题信息添加到数据框架
    df['dominant_topic'] = df['processed_content'].apply(get_dominant_topic)

    # 保存处理后的数据到新的 CSV 文件
    df.to_csv(output_file_path, index=False, encoding='utf-8-sig')

    print("主题提取完成，处理后的数据已保存至:", output_file_path)

    # 主题可视化部分
    visualize_topics(lda_model, corpus)

    # 新增：生成不同主题的词频CSV文件
    generate_topic_word_freq_csv(lda_model, dictionary, topic_word_freq_file_path)

def visualize_topics(lda_model, corpus):
    # 创建文件夹，如果它不存在
    output_dir = 'figures/wordcloud'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 可视化每个主题的关键词，生成词云
    for i, topic in lda_model.print_topics(num_topics=4, num_words=50):
        # 将主题编号从0开始调整为从1开始
        topic_number = i + 1
        print(f"主题 #{topic_number}: {topic}")
        
        # 处理主题的字符串格式
        words = topic.split(" + ")
        word_frequencies = {}

        # 提取每个词和它的权重
        for word in words:
            weight, word = word.split("*")
            word_frequencies[word.strip().strip('"')] = float(weight)

        # 生成词云
        wordcloud = WordCloud(width=1000,
                              height=700,
                              background_color='white',
                              font_path='simhei.ttf',
                              scale=15,
                              contour_width=5,
                              contour_color='red').generate_from_frequencies(word_frequencies)
        
        # 绘制词云
        plt.figure(figsize=(10, 10))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f"主题 #{topic_number} 词云")
        
        # 保存词云图到指定文件夹
        wordcloud_image_path = os.path.join(output_dir, f"topic_{topic_number}_wordcloud.png")
        plt.savefig(wordcloud_image_path, format='png')
        plt.close()
        print(f"主题 #{topic_number} 词云已保存至 {wordcloud_image_path}")

def generate_topic_word_freq_csv(lda_model, dictionary, output_file_path):
    # 获取每个主题的词频
    topic_word_freq = {}
    for topic_id in range(lda_model.num_topics):
        topic_word_freq[topic_id] = {}
        # 获取每个主题的前20个词语及其词频
        for word_id, freq in lda_model.get_topic_terms(topic_id, topn=20):
            word = dictionary[word_id]
            topic_word_freq[topic_id][word] = freq

    # 将词频数据转换为DataFrame
    df_topic_word_freq = pd.DataFrame(topic_word_freq).T

    # 确保每个主题至少有20个词语
    for topic_id in range(lda_model.num_topics):
        if len(df_topic_word_freq.columns) < 20:
            # 如果某个主题的词语不足20个，填充NaN
            df_topic_word_freq = df_topic_word_freq.reindex(columns=range(20), fill_value=None)

    # 调整列名和行名
    df_topic_word_freq.index.name = '主题编号'
    df_topic_word_freq.columns.name = '词汇'

    # 保存词频数据到CSV文件
    df_topic_word_freq.to_csv(output_file_path, encoding='utf-8-sig')
    print(f"不同主题的词频数据已保存至 {output_file_path}")

if __name__ == '__main__':
    main()