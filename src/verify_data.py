import sqlite3
from contextlib import closing
from tabulate import tabulate

def verify_data(db_path, table_name='sentiment_analysis', limit=5):
    """
    验证数据库中指定表是否包含数据，并打印前 limit 条记录。
    
    参数:
    db_path -- SQLite 数据库文件路径。
    table_name -- 要验证的数据表名称（默认: sentiment_analysis）
    limit -- 显示多少条数据（默认: 5）
    """
    try:
        with closing(sqlite3.connect(db_path)) as conn:
            with closing(conn.cursor()) as c:
                # 检查表是否存在
                c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
                if not c.fetchone():
                    print(f"❌ 错误：表 '{table_name}' 不存在，请检查数据库结构。")
                    return
                
                # 查询数据
                c.execute(f'PRAGMA table_info({table_name})')
                columns = [col[1] for col in c.fetchall()]

                c.execute(f'SELECT * FROM {table_name} LIMIT {limit}')
                rows = c.fetchall()

                if rows:
                    print(f"\n✅ 成功找到表 '{table_name}' 中的前 {limit} 条数据：\n")
                    print(tabulate(rows, headers=columns, tablefmt="grid"))
                else:
                    print("⚠️ 数据库表中没有数据，请检查数据导入过程。")

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")

# 示例调用
if __name__ == '__main__':
    db_file = 'data/sentiment_analysis.db'
    verify_data(db_file)