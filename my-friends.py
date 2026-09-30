from utils import init_browser, login_with_cookies, get_all_friends
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    browser, wait = init_browser(headless=True)
    try:
        login_with_cookies(browser, wait)
        get_all_friends(browser, wait)
    except Exception as e:
        print(f"\n[LỖI]: {e}")
        browser.quit()