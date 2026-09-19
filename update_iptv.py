import json
import time
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"

def get_headers(referer="https://google.com/"):
    return {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Accept": "*/*"
    }

def fetch_football_matches():
    print("⏳ Đang cào danh sách và cập nhật token cho các luồng IPTV...")
    
    m3u_lines = ["#EXTM3U\n"]
    
    # 1. Thêm kênh Test chuẩn luôn mở được
    m3u_lines.append('#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n')
    m3u_lines.append("http://cdn.vtvall.vn/vtv3/index.m3u8\n")

    sources = [
        {"name": "Xôi Lạc Z TV", "url": "https://api.xoilac.com/api/match/featured", "referer": "https://xoilac.com/"},
        {"name": "Bia Ôm TV", "url": "https://api.v2.xoilac.tv/api/match/featured", "referer": "https://xbdbotv.live/"},
        {"name": "Giờ Vàng TV", "url": "https://api.keobongvip.digital/api/matches", "referer": "https://keobongvip.digital/"}
    ]

    match_count = 0

    for src in sources:
        try:
            res = requests.get(src["url"], headers=get_headers(src["referer"]), impersonate="chrome120", timeout=8)
            if res.status_code == 200:
                data = res.json()
                items = data.get("data") or data.get("matches") or (data if isinstance(data, list) else [])

                for match in items:
                    home = match.get("home_name") or match.get("home", {}).get("name", "Đội nhà")
                    away = match.get("away_name") or match.get("away", {}).get("name", "Đội khách")
                    time_str = match.get("match_time") or match.get("time", "Đang đá")
                    blv = match.get("commentator") or match.get("blv", "BLV")
                    logo = match.get("logo") or match.get("home_logo") or ""
                    
                    is_live = match.get("is_live", False)
                    status = "🟢 LIVE" if is_live else "⏰"

                    links = match.get("play_urls") or match.get("links", []) or []
                    for idx, item in enumerate(links):
                        stream_url = ""
                        server = f"Server {idx+1}"

                        if isinstance(item, dict):
                            stream_url = item.get("url") or item.get("link", "")
                            server = item.get("name") or server
                        elif isinstance(item, str):
                            stream_url = item

                        if stream_url and stream_url.startswith("http"):
                            # Ưu tiên lấy định dạng m3u8 thay vì flv
                            logo_attr = f'tvg-logo="{logo}" ' if logo else ""
                            title = f"{status} [{time_str}] {home} vs {away} - {server} ({blv})"
                            
                            # Ghi cấu hình Header vào playlist để IPTV Player đọc được
                            m3u_lines.append(f'#EXTINF:-1 {logo_attr}group-title="{src["name"]}",{title}\n')
                            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                            m3u_lines.append(f'#EXTVLCOPT:http-referrer={src["referer"]}\n')
                            m3u_lines.append(f"{stream_url}\n")
                            match_count += 1
        except Exception as e:
            print(f"⚠️ Nguồn {src['name']} lỗi: {e}")

    # 2. Nếu tại thời điểm cào không có trận nào live, thêm kênh truyền hình thể thao dự phòng
    if match_count == 0:
        print("ℹ️ Hiện không có trận đấu trực tiếp, thêm danh sách kênh thể thao dự phòng...")
        backup_channels = [
            ("VTV5 HD - Thể Thao", "http://cdn.vtvall.vn/vtv5/index.m3u8"),
            ("VTV6 / VTV Cần Thơ", "http://cdn.vtvall.vn/vtv6/index.m3u8"),
        ]
        for name, url in backup_channels:
            m3u_lines.append(f'#EXTINF:-1 group-title="Thể Thao Dự Phòng",⚽ {name}\n')
            m3u_lines.append(f"{url}\n")

    return m3u_lines

def main():
    lines = fetch_football_matches()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🎉 Đã cập nhật xong file playlist.m3u lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if __name__ == "__main__":
    main()