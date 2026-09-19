import json
import re
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def fetch_data():
    now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    print(f"⏳ Đang thực hiện cào dữ liệu bóng đá lúc {now_str}...")
    
    # Thêm timestamp vào header file để ép Git nhận diện nội dung mới 100%
    m3u_lines = [
        "#EXTM3U\n",
        f'#EXTINF:-1 group-title="HỆ THỐNG",🔄 Cập nhật lần cuối: {now_str}\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n",
        '#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n"
    ]

    # Danh sách các API public lấy trận trực tiếp
    endpoints = [
        {
            "name": "Bia Ôm TV",
            "url": "https://api.xbdbotv.live/api/v1/match/list",
            "referer": "https://xbdbotv.live/"
        },
        {
            "name": "Xôi Lạc TV",
            "url": "https://api.xoilac.com/api/match/featured",
            "referer": "https://xoilac.com/"
        }
    ]

    count = 0
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    for ep in endpoints:
        try:
            res = requests.get(ep["url"], headers=headers, impersonate="chrome120", timeout=8)
            if res.status_code == 200:
                data = res.json()
                matches = data.get("data") or data.get("matches") or []
                
                for item in matches:
                    home = item.get("home_name") or item.get("home", {}).get("name", "Đội nhà")
                    away = item.get("away_name") or item.get("away", {}).get("name", "Đội khách")
                    time_val = item.get("time") or item.get("match_time", "Live")
                    blv = item.get("blv") or item.get("commentator", "")
                    
                    links = item.get("links") or item.get("play_urls") or []
                    for idx, link_item in enumerate(links):
                        stream_url = link_item.get("url") if isinstance(link_item, dict) else link_item
                        if stream_url and ("m3u8" in stream_url or "flv" in stream_url):
                            title = f"🟢 [{time_val}] {home} vs {away} - Link {idx+1}"
                            if blv:
                                title += f" ({blv})"
                            
                            m3u_lines.append(f'#EXTINF:-1 group-title="{ep["name"]}",{title}\n')
                            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                            m3u_lines.append(f'#EXTVLCOPT:http-referrer={ep["referer"]}\n')
                            m3u_lines.append(f"{stream_url}\n")
                            count += 1
        except Exception as e:
            print(f"⚠️ Lỗi cào {ep['name']}: {e}")

    print(f"✅ Tìm thấy {count} luồng trực tiếp.")
    return m3u_lines

def main():
    lines = fetch_data()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("🎉 Đã ghi xong file playlist.m3u!")

if __name__ == "__main__":
    main()