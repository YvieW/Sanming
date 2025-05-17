import pandas as pd
import sqlite3

def import_data_to_db(csv_file, db_path):
    # 读取CSV文件
    df = pd.read_csv(csv_file)
    
    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建数据库表（根据实际列名）
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sentiment_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cut_content TEXT,
        text TEXT,
        keyword1 TEXT,
        keyword2 TEXT,
        keyword3 TEXT,
        similarity_score REAL,
        processed_content TEXT,
        dominant_topic INTEGER,
        sentiment_score REAL,
        sentiment_label TEXT
    )
    ''')
    

    # 遍历数据框并插入数据
    for index, row in df.iterrows():
        cursor.execute('''
        INSERT INTO sentiment_analysis 
        (cut_content, text, keyword1, keyword2, keyword3, similarity_score, processed_content, dominant_topic, sentiment_score, sentiment_label)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (row['cut_content'], row['text'], row['keyword1'],row['keyword2'],row['keyword3'], row['similarity_score'],
              row['processed_content'], row['dominant_topic'], row['sentiment_score'], row['sentiment_label']))

    # 提交事务并关闭连接
    conn.commit()
    conn.close()
    print("数据已成功导入到数据库中。")

# 示例调用
csv_file = 'data/processed_data/sentiment_analysis_results.csv'
db_path = 'data/sentiment_analysis.db'
import_data_to_db(csv_file, db_path)