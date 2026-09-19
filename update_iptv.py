import asyncio
import re
from datetime import datetime
from playwright.async_api import async_playwright

async def capture_iptv_data():
    print("⏳ Đang bật Chromium ngầm để bóc tách token...")
    m3u_lines = ["#EXTM3U\n"]
    m3u_lines.append('#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n')
    m3u_lines.append("http://cdn.vtvall.vn/vtv3/index.m3u8\n")

    captured_entries = []
    sources = [
        {"name": "Bia Ôm TV", "url": "https://xbdbotv.live/"},
        {"name": "Xôi Lạc Z TV", "url": "https://xoilac365.tv/"},
        {"name": "Chuối Chiên TV", "url": "https://chuoichientv.net/"}
    ]

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )

            for src in sources:
                page = await context.new_page()
                def handle_response(response):
                    url = response.url
                    if (".m3u8" in url or ".flv" in url) and "vtv3" not in url:
                        captured_entries.append({"group": src["name"], "url": url})
                
                page.on("response", handle_response)
                try:
                    await page.goto(src["url"], wait_until="domcontentloaded", timeout=20000)
                    await page.wait_for_timeout(4000)
                    content = await page.content()
                    matches = re.findall(r'(https?://[^\s\'"]+\.(?:m3u8|flv)\?[^\s\'"]*|https?://[^\s\'"]+\.(?:m3u8|flv))', content)
                    for m_url in matches:
                        captured_entries.append({"group": src["name"], "url": m_url})
                except Exception as e:
                    print(f"⚠️ Bỏ qua {src['name']} do timeout/lỗi: {e}")
                finally:
                    await page.close()

            await browser.close()
    except Exception as e:
        print(f"⚠️ Lỗi khởi tạo Browser: {e}")

    # Lọc trùng
    unique_links = {}
    for entry in captured_entries:
        if entry["url"] not in unique_links:
            unique_links[entry["url"]] = entry["group"]

    total = 0
    for url, group in unique_links.items():
        total += 1
        m3u_lines.append(f'#EXTINF:-1 group-title="{group}",🟢 Trận Trực Tiếp {total}\n')
        m3u_lines.append(f"{url}\n")

    return m3u_lines

def main():
    try:
        lines = asyncio.run(capture_iptv_data())
    except Exception as e:
        print(f"🔥 Lỗi Fatal: {e}")
        lines = [
            "#EXTM3U\n",
            '#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n',
            "http://cdn.vtvall.vn/vtv3/index.m3u8\n"
        ]

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🎉 Hoàn thành ghi file playlist.m3u lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if __name__ == "__main__":
    main()