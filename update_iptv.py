import requests
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

SOURCE_URL = "https://thcoban.github.io/thtt/tttt.m3u"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def check_link_alive(channel):
    """Kiểm tra xem link luồng phát trực tiếp có còn sống hay không"""
    url = channel['url']
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": channel.get('referer', 'https://google.com')
    }
    
    try:
        # Gửi request HEAD/GET nhanh timeout 4 giây để kiểm tra luồng
        response = requests.get(url, headers=headers, stream=True, timeout=4, verify=False)
        if response.status_code == 200:
            return channel
    except Exception:
        pass
    return None

def parse_and_filter_m3u():
    print(f"⏳ Đang tải dữ liệu từ nguồn: {SOURCE_URL}...")
    try:
        res = requests.get(SOURCE_URL, timeout=10)
        res.encoding = 'utf-8'
        if res.status_code != 200:
            print("❌ Không thể tải được file nguồn.")
            return []
    except Exception as e:
        print(f"❌ Lỗi kết nối nguồn: {e}")
        return []

    lines = res.text.splitlines()
    raw_channels = []
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#EXTINF:"):
            extinf = line
            user_agent = USER_AGENT
            referer = "https://google.com"
            stream_url = ""
            
            # Đọc các thuộc tính bổ sung nếu có (#EXTVLCOPT)
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if next_line.startswith("#EXTVLCOPT:http-user-agent="):
                    user_agent = next_line.split("=", 1)[1]
                elif next_line.startswith("#EXTVLCOPT:http-referrer="):
                    referer = next_line.split("=", 1)[1]
                elif next_line and not next_line.startswith("#"):
                    stream_url = next_line
                    break
                j += 1
            
            if stream_url:
                raw_channels.append({
                    "extinf": extinf,
                    "user_agent": user_agent,
                    "referer": referer,
                    "url": stream_url
                })
            i = j
        i += 1

    print(f"📊 Tìm thấy {len(raw_channels)} kênh từ nguồn. Bắt đầu kiểm tra kênh sống...")

    # Sử dụng đa luồng (20 threads) để kiểm tra nhanh danh sách kênh
    alive_channels = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(check_link_alive, raw_channels)
        for res in results:
            if res:
                alive_channels.append(res)

    print(f"✅ Đã lọc xong: {len(alive_channels)}/{len(raw_channels)} kênh đang hoạt động tốt.")
    return alive_channels

def main():
    now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    alive_channels = parse_and_filter_m3u()

    m3u_lines = [
        "#EXTM3U\n",
        f'#EXTINF:-1 group-title="HỆ THỐNG",🔄 Cập nhật hệ thống: {now_str}\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n"
    ]

    for ch in alive_channels:
        m3u_lines.append(f"{ch['extinf']}\n")
        m3u_lines.append(f"#EXTVLCOPT:http-user-agent={ch['user_agent']}\n")
        m3u_lines.append(f"#EXTVLCOPT:http-referrer={ch['referer']}\n")
        m3u_lines.append(f"{ch['url']}\n")

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(m3u_lines)

if __name__ == "__main__":
    main()