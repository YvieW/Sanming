from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pickle
import time

def save_weibo_cookies():
    # 设置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")  # 最大化窗口
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # 防止检测自动化

    # 使用 webdriver-manager 自动管理 ChromeDriver
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)

    try:
        # 打开微博登录页面
        print("正在打开微博登录页面...")
        driver.get("https://weibo.com/login.php")

        # 等待用户手动登录
        print("请手动登录微博，登录完成后按 Enter 键继续...")
        input("登录完成后，按 Enter 键继续...")

        # 获取当前页面的所有 cookies
        cookies = driver.get_cookies()

        # 将 cookies 保存到文件
        with open("cookies.pkl", "wb") as file:
            pickle.dump(cookies, file)
        print("Cookies 已成功保存到 cookies.pkl 文件中")

    finally:
        driver.quit()

if __name__ == "__main__":
    save_weibo_cookies()