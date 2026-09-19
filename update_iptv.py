import asyncio
import json
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def capture_iptv_data():
    print("⏳ Đang mở trình duyệt Chrome ngầm để bắt API Token...")
    
    m3u_lines = ["#EXTM3U\n"]
    m3u_lines.append('#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n')
    m3u_lines.append("http://cdn.vtvall.vn/vtv3/index.m3u8\n")

    captured_entries = []

    # Danh sách các web nguồn
    sources = [
        {"name": "Bia Ôm TV", "url": "https://xbdbotv.live/"},
        {"name": "Xôi Lạc Z TV", "url": "https://xoilac365.tv/"},
        {"name": "Chuối Chiên TV", "url": "https://chuoichientv.net/"}
    ]

    async with async_playwright() as p:
        # Khởi tạo trình duyệt Chromium giả lập máy tính thật
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )

        for src in sources:
            print(f"🔍 Đang quét nguồn: {src['name']}...")
            page = await context.new_page()

            # Lắng nghe các Request API ngầm mà web gọi
            def handle_response(response):
                try:
                    # Nếu phát hiện request chứa file m3u8 hoặc flv có token
                    url = response.url
                    if (".m3u8" in url or ".flv" in url) and "vtv3" not in url:
                        captured_entries.append({
                            "group": src["name"],
                            "url": url
                        })
                except Exception:
                    pass

            page.on("response", handle_response)

            try:
                # Truy cập web và chờ Javascript chạy xong
                await page.goto(src["url"], wait_until="networkidle", timeout=25000)
                await page.wait_for_timeout(5000) # Đợi 5s cho API giải mã xong
                
                # Trích xuất thêm từ biến toàn cục window trên trang web
                content = await page.content()
                matches = re.findall(r'(https?://[^\s\'"]+\.(?:m3u8|flv)\?[^\s\'"]*|https?://[^\s\'"]+\.(?:m3u8|flv))', content)
                for m_url in matches:
                    captured_entries.append({
                        "group": src["name"],
                        "url": m_url
                    })

            except Exception as e:
                print(f"⚠️ Không thể tải {src['name']}: {e}")
            finally:
                await page.close()

        await browser.close()

    # Lọc trùng lặp URL
    unique_links = {}
    for entry in captured_entries:
        url = entry["url"]
        if url not in unique_links:
            unique_links[url] = entry["group"]

    # Ghi vào M3U
    total = 0
    for url, group in unique_links.items():
        total += 1
        title = f"🟢 Trận Trực Tiếp {total}"
        m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{title}\n')
        m3u_lines.append(f"{url}\n")

    print(f"✅ Đã thu thập thành công {total} luồng live có Token thật.")
    return m3u_lines

def main():
    lines = asyncio.run(capture_iptv_data())
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🎉 Hoàn tất lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if __name__ == "__main__":
    main()