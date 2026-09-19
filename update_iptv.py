import re
import json
import time
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# Danh sách mẫu gốc chuẩn (Master List) dùng làm bộ khung khi API ngoài bị Cloudflare chặn IP máy chủ
MASTER_M3U_RAW = """
#EXTINF:-1 tvg-logo="https://d1c0s7hi3ugzoc.cloudfront.net/teams/genoa-102" group-title="Bia Ôm TV",🟡 23:00 15/09 ⚽ Genoa vs Südtirol (Lẩu Ếch) [hls]
https://cdnhls.xbdbotv.live/live/MTk3MjgzNzM6YThsY2E2YTk4dWpna3Q2bXcydDZwYXRxOnplMHpzd3lvYXRyd25xNzQxcHhjNGpyYw/index.m3u8
#EXTINF:-1 tvg-logo="https://d1c0s7hi3ugzoc.cloudfront.net/teams/al-ain-7780" group-title="Bia Ôm TV",🟡 23:00 15/09 ⚽ Al Ain vs Al Nassr (NEM NƯỚNG) [hls]
https://cdnhls.xbdbotv.live/live/MTk4NjcwNDc6dWppY2ViaXFnN2Fmazdhendla3Q3azE3OmR1NDE5eDRxN3J6MGQ3bDEya2xyajhoMg/index.m3u8
#EXTINF:-1 tvg-logo="https://imgts.sportpulseapiz.com/football/team/4wyrn4h850yq86p/image/small" group-title="Xôi Lạc Z TV",🟡 23:00 15/09 ⚽ Al-Ain FC vs Al Nassr (ROY)
https://live2.zundrixmediapipeline.com/live/channel1.flv
#EXTINF:-1 tvg-logo="https://media.chuoichientv.net/media/uploads/20250623_142148_996053df.png" group-title="Chuối Chiên TV",🟢 20:45 15/09 ⚽ Arkadag vs Muharraq (Chuối Lá) [FHD] [hls]
https://stm9ee346727718.stream.hdplaylink.com/cctvlive/chuoilahd/playlist.m3u8
"""

def fetch_live_data():
    now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    print(f"⏳ Bắt đầu quét dữ liệu IPTV lúc {now_str}...")
    
    m3u_lines = [
        "#EXTM3U\n",
        f'#EXTINF:-1 group-title="HỆ THỐNG",🔄 Cập nhật hệ thống: {now_str}\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n"
    ]

    fetched_items = []

    # API Endpoints lấy danh sách kèm Title + Token
    sources = [
        {
            "group": "Bia Ôm TV",
            "url": "https://api.xbdbotv.live/api/v1/match/live-streams",
            "referer": "https://xbdbotv.live/"
        },
        {
            "group": "Xôi Lạc Z TV",
            "url": "https://api.zundrixmediapipeline.com/api/v1/live",
            "referer": "https://xoilac.com/"
        }
    ]

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://google.com"
    }

    # THỬ PHƯƠNG ÁN 1: CÀO TRỰC TIẾP TỪ API
    for src in sources:
        try:
            res = requests.get(src["url"], headers=headers, impersonate="chrome120", timeout=8)
            if res.status_code == 200:
                data = res.json()
                items = data.get("data") or data.get("rows") or []
                for it in items:
                    title = it.get("title") or f"{it.get('home_name', '')} vs {it.get('away_name', '')}"
                    logo = it.get("logo") or it.get("home_logo") or ""
                    stream = it.get("play_url") or it.get("stream_url") or it.get("url")
                    
                    if stream and title:
                        fetched_items.append({
                            "logo": logo,
                            "group": src["group"],
                            "title": title,
                            "url": stream,
                            "referer": src["referer"]
                        })
        except Exception as e:
            print(f"⚠️ API {src['group']} không phản hồi (có thể bị chặn IP): {e}")

    # PHƯƠNG ÁN 2: NẾU API NGOÀI LỖI -> DÙNG MASTER LIST VÀ LÀM MỚI TOKEN TỰ ĐỘNG
    if not fetched_items:
        print("💡 API trực tiếp bị cản bởi Cloudflare! Chuyển sang bóc tách Master List & Re-tokenize...")
        raw_entries = MASTER_M3U_RAW.strip().split("#EXTINF:-1")
        
        for entry in raw_entries:
            if not entry.strip():
                continue
            lines = entry.strip().split("\n")
            if len(lines) >= 2:
                extinf = lines[0]
                stream_url = lines[1].strip()
                
                # Bóc logo, group, title từ chuỗi EXTINF cũ
                logo_match = re.search(r'tvg-logo="([^"]+)"', extinf)
                group_match = re.search(r'group-title="([^"]+)"', extinf)
                title_match = re.search(r',(.*)$', extinf)

                logo = logo_match.group(1) if logo_match else ""
                group = group_match.group(1) if group_match else "BÓNG ĐÁ LIVE"
                title = title_match.group(1).strip() if title_match else "Trận đấu Trực tiếp"

                # Cập nhật Token mới theo timestamp thực tế tránh bị dính token hết hạn
                if "auth_key=" in stream_url:
                    current_ts = int(time.time()) + 21600 # Cộng 6 tiếng hạn token
                    stream_url = re.sub(r'auth_key=\d+', f'auth_key={current_ts}', stream_url)

                fetched_items.append({
                    "logo": logo,
                    "group": group,
                    "title": title,
                    "url": stream_url,
                    "referer": "https://google.com"
                })

    # XUẤT RA CHUẨN ĐỊNH DẠNG M3U DÀNH CHO IPTV
    for item in fetched_items:
        logo_str = f' tvg-logo="{item["logo"]}"' if item["logo"] else ""
        m3u_lines.append(f'#EXTINF:-1{logo_str} group-title="{item["group"]}",{item["title"]}\n')
        m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
        m3u_lines.append(f'#EXTVLCOPT:http-referrer={item["referer"]}\n')
        m3u_lines.append(f"{item['url']}\n")

    print(f"🎉 Đã tạo thành công {len(fetched_items)} kênh live đầy đủ Title và Logo!")
    return m3u_lines

def main():
    lines = fetch_live_data()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)

if __name__ == "__main__":
    main()