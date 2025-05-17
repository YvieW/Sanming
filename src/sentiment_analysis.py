import pandas as pd
from snownlp import SnowNLP
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib import font_manager

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体（SimHei）
plt.rcParams['axes.unicode_minus'] = False  # 解决负号 '-' 显示为方块的问题
# 读取 topic_extracted_comments.csv 文件
input_file_path = os.path.join('data', 'topic_extracted_comments.csv')
output_file_path = os.path.join('data', 'sentiment_analysis_results.csv')

# 加载数据
df = pd.read_csv(input_file_path)

# 查看数据框架前几行，了解数据结构
print("数据框架预览:")
print(df.head())

# 定义一个函数来获取每个评论的情感分数
def analyze_sentiment(text):
    if isinstance(text, str):
        # 使用 SnowNLP 分析情感
        s = SnowNLP(text)
        return s.sentiments  # 返回情感分数，范围在 0 到 1 之间
    return None

# 为每个评论添加情感分数
df['sentiment_score'] = df['final_content'].apply(analyze_sentiment)

# 分配情感标签
def sentiment_label(score):
    if score >= 0.6:  # 高于 0.6 视为正面
        return 'Positive'
    elif score <= 0.4:  # 低于 0.4 视为负面
        return 'Negative'
    else:
        return 'Neutral'  # 中间值视为中性

df['sentiment_label'] = df['sentiment_score'].apply(sentiment_label)

# 按主题分类的情感分析
sentiment_by_topic = df.groupby(['dominant_topic', 'sentiment_label']).size().unstack(fill_value=0)

# 可视化每个主题的情感分布
plt.figure(figsize=(12, 8))
sns.set_palette("Set2")

# 绘制每个主题的情感分布条形图
sentiment_by_topic.plot(kind='bar', stacked=True, figsize=(12, 8))
plt.title('每个主题的情感分布', fontsize=16)
plt.xlabel('主题', fontsize=14)
plt.ylabel('评论数', fontsize=14)
plt.xticks(rotation=0)
plt.legend(title='情感标签', fontsize=12)
plt.tight_layout()

# 保存图形
output_dir = 'figures/sentiment_analysis'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

sentiment_plot_path = os.path.join(output_dir, 'sentiment_distribution.png')
plt.savefig(sentiment_plot_path)
plt.show()

# 输出情感分析结果到新的 CSV 文件
df.to_csv(output_file_path, index=False, encoding='utf-8-sig')
print("情感分析完成，结果已保存至:", output_file_path)

# 进一步细致的情感分析可视化
plt.figure(figsize=(12, 8))
sns.boxplot(data=df, x='dominant_topic', y='sentiment_score', palette="Set2")
plt.title('每个主题的情感得分分布', fontsize=16)
plt.xlabel('主题', fontsize=14)
plt.ylabel('情感得分', fontsize=14)
plt.xticks(rotation=0)
plt.tight_layout()

# 保存情感得分分布的箱型图
sentiment_boxplot_path = os.path.join(output_dir, 'sentiment_boxplot.png')
plt.savefig(sentiment_boxplot_path)
plt.show()