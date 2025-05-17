from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
import csv
import requests
from datetime import datetime

def scrape_wechat(keyword, save_dir='data/WeChatSougo', max_articles=15, max_pages=2):
    # 创建保存目录
    os.makedirs(save_dir, exist_ok=True)

    # 设置无头模式浏览器
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    # 启动浏览器
    driver = webdriver.Chrome(options=chrome_options)
    
    print(f"[INFO] 正在搜索关键词：{keyword}")
    search_url = f"https://weixin.sogou.com/weixin?type=2&query={keyword}"
    driver.get(search_url)

    time.sleep(5)  # 等待页面加载

    # 检查页面是否正确加载
    if "抱歉，未找到与" in driver.page_source:
        print(f"[WARNING] 搜索结果为空，未找到与关键词 '{keyword}' 相关的文章。")
        driver.quit()
        return []

    all_texts = []
    csv_file = os.path.join(save_dir, 'articles.csv')
    with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:  # 使用utf-8-sig编码
        csv_writer = csv.writer(f)
        csv_writer.writerow(['Time', 'Place', 'Content', 'Source', 'Comments'])

        page = 1
        while page <= max_pages:
            print(f"[INFO] 正在处理第 {page} 页")
            # 获取当前页的所有文章链接
            articles = driver.find_elements(By.CSS_SELECTOR, '.news-list li .txt-box h3 a')
            article_links = [a.get_attribute('href') for a in articles[:max_articles]]

            # 新增调试输出
            print(f"[INFO] 共提取到 {len(article_links)} 个链接：")
            for i, link in enumerate(article_links):
                print(f"[{i+1}] {link}")

            for i, link in enumerate(article_links):
                print(f"[INFO] 正在抓取文章 {i+1}：{link}")
                try:
                    driver.get(link)
                    time.sleep(3)

                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')

                    # 提取主要正文内容（公众号文章通常在 #js_content）
                    content_div = soup.find(id='js_content')
                    if content_div:
                        title = soup.find('h2', class_='rich_media_title').get_text(strip=True)
                        text = content_div.get_text(separator='\n').strip()

                        # 提取评论
                        comments = []
                        comment_section = soup.find('div', class_='rich_media_comment_list')
                        if comment_section:
                            comment_items = comment_section.find_all('li', class_='comment_item')
                            for item in comment_items:
                                comment_text = item.find('span', class_='comment_content').get_text(strip=True)
                                comments.append(comment_text)

                        # 提取时间、来源等信息
                        time_tag = soup.find('em', id='post-date')
                        time_str = time_tag.get_text(strip=True) if time_tag else "N/A"
                        place_tag = soup.find('a', class_='rich_media_meta rich_media_meta_link rich_media_meta_nickname')
                        place_str = place_tag.get_text(strip=True) if place_tag else "N/A"
                        source_tag = soup.find('a', class_='rich_media_meta rich_media_meta_link rich_media_meta_nickname')
                        source_str = source_tag.get_text(strip=True) if source_tag else "N/A"

                        # 保存到CSV文件
                        csv_writer.writerow([time_str, place_str, text, source_str, '\n'.join(comments)])

                        # 保存到单独的文本文件
                        filename = os.path.join(save_dir, f'article_{i+1}.txt')
                        with open(filename, 'w', encoding='utf-8') as f:  # 使用utf-8编码
                            f.write(text)
                        all_texts.append(text)
                    else:
                        print(f"[WARNING] 未找到正文内容。")
                except Exception as e:
                    print(f"[ERROR] 抓取失败：{e}")

            # 翻页
            try:
                next_page_link = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.LINK_TEXT, '下一页'))
                )
                if next_page_link and page < max_pages:
                    next_page_link.click()
                    time.sleep(5)  # 等待页面加载
                else:
                    break
            except Exception as e:
                print(f"[WARNING] 无法找到翻页链接或已到达最后一页：{e}")
                break

            page += 1

    driver.quit()
    return all_texts

# 示例调用
if __name__ == "__main__":
    keyword = "三明医改"
    scrape_wechat(keyword, max_pages=2)