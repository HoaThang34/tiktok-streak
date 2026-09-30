from utils import init_browser, save_cookies
import sys

def main():
    print("=" * 60)
    print(" CÔNG CỤ ĐĂNG NHẬP VÀ LƯU COOKIES TIKTOK")
    print("=" * 60)
    print("1. Đang mở trình duyệt Chrome...")
    browser, wait = init_browser(headless=False)

    try:
        browser.get("https://www.tiktok.com/login")
        print("\n2. Trình duyệt đã mở!")
        print("-> Bạn có thể đăng nhập bằng bất kỳ cách nào:")
        print("   + Quét mã QR bằng ứng dụng TikTok trên điện thoại (Nhanh nhất)")
        print("   + Đăng nhập qua Google / Facebook")
        print("   + Đăng nhập bằng Số điện thoại / Email")
        print("-" * 60)
        input(">> SAU KHI ĐĂNG NHẬP THÀNH CÔNG, HÃY NHẤN [ENTER] TẠI ĐÂY ĐỂ LƯU COOKIES << ")
        
        save_cookies(browser, "cookies.json")
        print("\n[THÀNH CÔNG] Cookies đã được lưu vào 'cookies.json'!")
        print("Từ bây giờ bạn có thể chạy 'python main.py' mà không cần nhập mật khẩu hay giải captcha nữa.")
    except Exception as e:
        print(f"\n[LỖI] Có lỗi xảy ra: {e}", file=sys.stderr)
    finally:
        browser.quit()

if __name__ == "__main__":
    main()
