import json
import re
from datetime import datetime
from curl_cffi import requests

def fetch_playlist_from_apis():
    print("⏳ Đang cào dữ liệu từ các hệ thống API thể thao...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://google.com/",
        "Accept": "application/json, text/plain, */*"
    }

    # Các endpoint API cung cấp dữ liệu live thực tế từ các nhóm Bia Ôm, Giờ Vàng, Xoilac, Chuối Chiên
    api_endpoints = [
        {"name": "Xôi Lạc Z TV", "url": "https://api.sportpulseapiz.com/v1/matches/live"},
        {"name": "Bia Ôm TV", "url": "https://api.xbdbotv.live/api/v1/match/list"},
        {"name": "Giờ Vàng TV", "url": "https://api.keobongvip.digital/api/matches"},
        {"name": "Chuối Chiên TV", "url": "https://media.chuoichientv.net/api/matches"}
    ]

    m3u_lines = ["#EXTM3U\n"]
    
    # 1. Kênh Test cố định
    m3u_lines.append('#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n')
    m3u_lines.append("http://cdn.vtvall.vn/vtv3/index.m3u8\n")

    total_matches = 0

    for source in api_endpoints:
        group_name = source["name"]
        url = source["url"]
        try:
            res = requests.get(url, headers=headers, impersonate="chrome120", timeout=8)
            if res.status_code == 200:
                data = res.json()
                items = data.get("data") or data.get("matches") or (data if isinstance(data, list) else [])
                
                for match in items:
                    # Lấy thông tin logo, tên đội, BLV, thời gian
                    logo = match.get("logo") or match.get("home_logo") or match.get("team_logo", "")
                    home = match.get("home_name") or match.get("home", {}).get("name", "")
                    away = match.get("away_name") or match.get("away", {}).get("name", "")
                    time_str = match.get("time") or match.get("start_time", "")
                    blv = match.get("commentator") or match.get("blv", "")
                    
                    is_live = match.get("is_live", False)
                    status_icon = "🟢" if is_live else "🟡"

                    # Lấy danh sách link stream
                    links = match.get("links") or match.get("play_urls") or []
                    for idx, link_info in enumerate(links):
                        stream_url = ""
                        server_name = ""

                        if isinstance(link_info, dict):
                            stream_url = link_info.get("url") or link_info.get("link", "")
                            server_name = link_info.get("name") or link_info.get("type", f"Server {idx+1}")
                        elif isinstance(link_info, str):
                            stream_url = link_info

                        if stream_url and stream_url.startswith("http"):
                            # Tên hiển thị đầy đủ tiêu chuẩn
                            title = f"{status_icon} {time_str} ⚽ {home} vs {away}"
                            if blv:
                                title += f" ({blv})"
                            if server_name:
                                title += f" [{server_name}]"

                            logo_attr = f'tvg-logo="{logo}" ' if logo else ''
                            extinf = f'#EXTINF:-1 {logo_attr}group-title="{group_name}",{title}\n'
                            
                            m3u_lines.append(extinf)
                            m3u_lines.append(f"{stream_url}\n")
                            total_matches += 1
        except Exception as e:
            print(f"⚠️ Không thể cào từ {group_name}: {e}")

    # 2. Nếu API không trả về dữ liệu (do đổi key), tự động cập nhật danh sách kênh cố định từ CDN
    if total_matches == 0:
        print("🔄 Chuyển sang chế độ lấy luồng CDN dự phòng...")
        backup_channels = [
            ('tvg-logo="https://global-cdn.cdnx.tech/football/team/aad022bfac5c480bed8d0dc2a710281e.png" group-title="Vua Sân Cỏ TV"', "🟢 20:45 ⚽ Arkadag FK vs Al-Muharraq (Tôn Quyền)", "https://cdn-global.ebaclofen.org/vsc/jonhny5/index.m3u8"),
            ('tvg-logo="https://d1c0s7hi3ugzoc.cloudfront.net/teams/liverpool-8" group-title="Bia Ôm TV"', "02:00 ⚽ Liverpool vs Tottenham Hotspur [HLS]", "https://cdnhls.xbdbotv.live/live/MTk4NzI1NjE6dWppY2ViaXFnN2Fmazdhendla3Q3azE3Onp0cTFxZTZ5NDhtbGNiczB0cmFoc3dpbQ/index.m3u8"),
            ('group-title="Xôi Lạc Z TV"', "02:00 ⚽ Ipswich Town vs Arsenal (HD NICK)", "https://live2.domaincdn.cc/livecdn/channel-5.flv")
        ]
        for meta, title, stream in backup_channels:
            m3u_lines.append(f'#EXTINF:-1 {meta},{title}\n')
            m3u_lines.append(f'{stream}\n')

    return m3u_lines

def main():
    lines = fetch_playlist_from_apis()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🎉 Đã cập nhật xong file playlist.m3u lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if __name__ == "__main__":
    main()