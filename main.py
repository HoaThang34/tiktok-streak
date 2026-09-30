from utils import init_browser, login_with_cookies, auto_send_message
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    browser, wait = init_browser(headless=True)
    try:
        login_with_cookies(browser, wait)
        auto_send_message(browser, wait)
    except Exception as e:
        print(f"\n[LỖI]: {e}")
        browser.quit()
