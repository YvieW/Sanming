from flask import Flask, render_template, request, send_from_directory, jsonify
import os
import sqlite3
import webbrowser
import threading
import requests
import time

ZHIPU_API_KEY = "2e1c8e08b8d540d898762d12e1a00540.GiLNydulGj9G8qU4"
ZHIPU_API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

app = Flask(__name__)

# 获取项目根目录（Sanming/）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 图像与数据库路径
wordcloud_dir = os.path.join(BASE_DIR, 'figures', 'wordcloud')
sentiment_dir = os.path.join(BASE_DIR, 'figures', 'sentiment_analysis')
DATABASE = os.path.join(BASE_DIR, 'data', 'sentiment_analysis.db')

# 三明医改政策说明
policy_summary = {
    "title": "三明医改政策概要",
    "overview": "三明医改是一项以控制医疗费用和推进医保支付方式改革为核心的系统性改革，始于2012年，在全国范围内具有示范意义。",
    "details": """
        <p>三明医改起源于福建省三明市，是中国医疗体制改革中的典型案例。其核心目标是解决看病贵、看病难问题，通过控制药价、改革医院收入结构、提高医保基金效率等手段，实现全民医疗保障体系的优化。</p>
        <ul>
            <li><strong>起始背景：</strong>医保资金面临巨大缺口，医院过度医疗问题严重。</li>
            <li><strong>关键改革：</strong>药品零加成、医疗服务价格调整、医生绩效薪酬制度改革、医保按病种付费等。</li>
            <li><strong>代表文件：</strong>
                <ul>
                    <li><a href="http://www.nhc.gov.cn" target="_blank">国家卫健委关于推广三明医改经验的通知</a></li>
                    <li><a href="http://www.sanming.gov.cn" target="_blank">三明市人民政府官网</a></li>
                </ul>
            </li>
        </ul>
    """
}

# 结构化主题解读内容
topic_insights = [
    {
        "title": "主题 1：医生职业困境与转行意愿",
        "image": "topic_1_wordcloud.png",
        "summary": "该主题集中体现医生对收入、晋升、未来前景的焦虑，‘转行’‘行政’‘三甲’等词突出了医疗体制内卷和出路迷茫。",
        "sentiment": "偏负面，情绪带有调侃、焦虑。",
    },
    {
        "title": "主题 2：薪资不公与劳动强度反差",
        "image": "topic_2_wordcloud.png",
        "summary": "‘哭’‘夜班’‘绩效’显示出医务人员的过劳与收入落差，引发强烈情绪反应与制度不公的讨论。",
        "sentiment": "情绪明显负面，充满抱怨与不满。",
    },
    {
        "title": "主题 3：冷门岗位的边缘化与无力感",
        "image": "topic_3_wordcloud.png",
        "summary": "以‘麻醉’‘医技’等关键词为核心，揭示某些科室和岗位在制度中的被忽视状态，伴随自嘲和无奈情绪。",
        "sentiment": "负面偏讽刺，反映边缘从业者的现实挣扎。",
    },
    {
        "title": "主题 4：医改落地效果与公众期待落差",
        "image": "topic_4_wordcloud.png",
        "summary": "‘失望’‘疗效’‘满意度’等词反映出医患双方对三明医改实际成效的反思与批评。",
        "sentiment": "批判性较强，整体情绪偏消极。",
    }
]


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    conn = get_db()

    wordcloud_images = sorted([f for f in os.listdir(wordcloud_dir) if f.endswith('.png')])
    sentiment_images = sorted([f for f in os.listdir(sentiment_dir) if f.endswith('.png')])

    cursor = conn.cursor()
    cursor.execute('SELECT cut_content FROM sentiment_analysis LIMIT 10')
    comments = cursor.fetchall()

    cursor.execute('''
        SELECT keyword, COUNT(*) as count FROM (
            SELECT keyword1 AS keyword FROM sentiment_analysis
            UNION ALL
            SELECT keyword2 FROM sentiment_analysis
            UNION ALL
            SELECT keyword3 FROM sentiment_analysis
        )
        GROUP BY keyword
        ORDER BY count DESC
        LIMIT 20
    ''')
    keywords = cursor.fetchall()

    conn.close()

    return render_template('index.html',
                           wordcloud_images=wordcloud_images,
                           sentiment_images=sentiment_images,
                           comments=comments,
                           keywords=keywords,
                           policy=policy_summary,
                           topic_insights=topic_insights)


@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword', '').strip()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT cut_content, text, keyword1, keyword2, keyword3, similarity_score, processed_content, dominant_topic, sentiment_score, sentiment_label
        FROM sentiment_analysis
        WHERE text LIKE ? OR keyword1 LIKE ? OR keyword2 LIKE ? OR keyword3 LIKE ?
    ''', tuple(['%' + keyword + '%'] * 4))
    search_results = cursor.fetchall()

    if search_results:
        dominant_topic = search_results[0]['dominant_topic']
        cursor.execute('''
            SELECT cut_content, text, keyword1, keyword2, keyword3, similarity_score, processed_content, dominant_topic, sentiment_score, sentiment_label
            FROM sentiment_analysis
            WHERE dominant_topic = ?
        ''', (dominant_topic,))
        same_topic_comments = cursor.fetchall()

        positive = sum(1 for r in search_results if r['sentiment_label'] == 'Positive')
        neutral = sum(1 for r in search_results if r['sentiment_label'] == 'Neutral')
        negative = sum(1 for r in search_results if r['sentiment_label'] == 'Negative')
        total_comments = len(search_results)

        api_summary = (
            f"搜索关键词 '{keyword}' 共找到 {total_comments} 条评论，"
            f"其中正面评论 {positive} 条，中性评论 {neutral} 条，负面评论 {negative} 条。"
        )
        structured_analysis = ""
    else:
        same_topic_comments = []
        positive = neutral = negative = total_comments = 0
        api_summary = f"未找到与关键词 '{keyword}' 相关的评论。"
        structured_analysis = "无相关数据，无法生成结构化主题分析。"

    conn.close()

    summary_stats = {
        "total_comments": total_comments,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "api_summary": api_summary,
    }

    return render_template('search_results.html',
                           keyword=keyword,
                           search_results=search_results,
                           same_topic_comments=same_topic_comments,
                           summary_stats=summary_stats,
                           structured_analysis=structured_analysis)


@app.route('/analyze_topics', methods=['POST'])
def analyze_topics():
    data = request.json
    keyword = data.get('keyword', '')
    comments = data.get('comments', [])

    prompt = f"""
结合三明医改的具体政策条例辅助分析，针对以下用户评论，进行结构化主题分析：
评论列表：
{comments}

格式要求：
一、主题分布
二、主题关联性分析
三、政策舆情分析与解读
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {ZHIPU_API_KEY}"
    }
    payload = {
        "model": "glm-4",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "top_p": 0.95,
        "max_tokens": 1500
    }
    max_retries = 3  # 最大重试次数
    retry_delay = 5  # 重试间隔时间（秒）

    for attempt in range(max_retries):
        try:
            response = requests.post(ZHIPU_API_URL, json=payload, headers=headers, timeout=120)  # 增加超时时间
            response.raise_for_status()
            result = response.json()
            analysis_text = result['choices'][0]['message']['content']
            return jsonify({"analysis": analysis_text})
        except requests.exceptions.Timeout as e:
            print(f"请求超时，正在尝试第 {attempt + 1} 次重试...")
            time.sleep(retry_delay)
        except requests.exceptions.RequestException as e:
            analysis_text = f"调用结构化主题分析接口失败：{str(e)}"
            return jsonify({"analysis": analysis_text})

    analysis_text = "调用结构化主题分析接口失败：重试次数已达上限，仍然无法获取结果。"
    return jsonify({"analysis": analysis_text})


@app.route('/figures/<folder>/<filename>')
def serve_image(folder, filename):
    folder_path = os.path.join(BASE_DIR, 'figures', folder)
    return send_from_directory(folder_path, filename)


def open_browser():
    webbrowser.open_new('http://127.0.0.1:5000')


if __name__ == '__main__':
    threading.Timer(0.5, open_browser).start()
    app.run(debug=True)
