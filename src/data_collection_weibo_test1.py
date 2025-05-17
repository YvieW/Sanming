import time
import csv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

def collect_weibo_posts():
    # 设置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # 最大化窗口
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 防止检测自动化

    # 设置 driver 路径
    service = Service(executable_path="./chromedriver.exe")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # 打开微博登录页面
        print("正在打开微博登录页面...")
        driver.get("https://weibo.com/login.php")

        # 等待用户手动登录
        print("请手动登录微博，登录完成后按 Enter 键继续...")
        input("登录完成后，按 Enter 键继续...")

        # 2. 查找搜索框并输入关键词
        print("页面加载完成，查找搜索框...")
        try:
            # 增加等待时间，确保页面完全加载
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.XPATH, "//input[@class='searchInp_form']"))
            )
            search_box = driver.find_element(By.XPATH, "//input[@class='searchInp_form']")
        except Exception as e:
            print(f"[错误] 搜索框未能加载: {e}")
            return

        search_box.send_keys("三明医改")
        time.sleep(2)

        # 使用 ActionChains 模拟回车键
        actions = ActionChains(driver)
        actions.send_keys(Keys.ENTER).perform()

        # 3. 等待搜索结果加载
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, "card"))
            )
        except Exception as e:
            print(f"[错误] 搜索结果加载失败: {e}")
            return

        # 4. 获取前几条微博卡片
        time.sleep(3)
        posts = driver.find_elements(By.CLASS_NAME, "card")[:5]  # 抓取前5条微博

        all_data = []

        for i, post in enumerate(posts):
            try:
                # 抓取主帖文本
                content_elem = post.find_element(By.CLASS_NAME, "txt")
                post_text = content_elem.text

                # 模拟点击“评论”按钮
                try:
                    comment_button = post.find_element(By.PARTIAL_LINK_TEXT, "评论")
                    comment_button.click()
                    time.sleep(2)
                except:
                    print(f"[警告] 第{i+1}条微博找不到评论按钮")
                    continue

                # 切换评论 iframe（如果有）
                try:
                    driver.switch_to.frame("plc_main")  # 如果微博使用 iframe 来显示评论
                except:
                    pass

                # 抓取评论内容
                comments = driver.find_elements(By.CLASS_NAME, "txt")
                comments_text = [c.text for c in comments[:20]]  # 抓20条评论

                for comment in comments_text:
                    all_data.append([post_text, comment])

            except Exception as e:
                print(f"[错误] 抓取第{i+1}条微博失败: {e}")

        # 5. 保存数据到 CSV
        with open("./data/weibo_sanming_comments.csv", mode="w", encoding="utf-8-sig", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["微博内容", "评论"])
            writer.writerows(all_data)

        print("✅ 抓取完成，数据已保存至 data/weibo_sanming_comments.csv")

    finally:
        driver.quit()

if __name__ == "__main__":
    collect_weibo_posts()
