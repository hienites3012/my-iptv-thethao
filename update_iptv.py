import os
import re
import json
import time
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

def get_headers(referer="https://google.com"):
    return {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Accept": "application/json, text/plain, */*",
        "Origin": referer.rstrip("/")
    }

def parse_xoilac_matches():
    """Cào danh sách trận đấu + link xem mới nhất từ hệ thống Xôi Lạc / Bánh Mì / Bia Ôm"""
    matches = []
    
    # Danh sách các Gateway API cập nhật trận đấu theo ngày
    api_endpoints = [
        {
            "group": "Xôi Lạc TV",
            "url": "https://api.vebo.xyz/api/match/featured",
            "referer": "https://vebo.xyz/"
        },
        {
            "group": "Bia Ôm TV",
            "url": "https://api.xbdbotv.live/api/v1/match/live-streams",
            "referer": "https://xbdbotv.live/"
        }
    ]

    for ep in api_endpoints:
        try:
            res = requests.get(ep["url"], headers=get_headers(ep["referer"]), impersonate="chrome120", timeout=10)
            if res.status_code != 200:
                continue
            
            data = res.json()
            items = data.get("data") or data.get("rows") or (data if isinstance(data, list) else [])

            for match in items:
                # Bóc tách thông tin trận đấu
                home = match.get("home_name") or match.get("homeTeam", {}).get("name", "Home")
                away = match.get("away_name") or match.get("awayTeam", {}).get("name", "Away")
                commentator = match.get("commentator") or match.get("blv") or match.get("author", "")
                
                # Giờ thi đấu
                match_time = match.get("match_time") or match.get("time", "")
                if isinstance(match_time, (int, float)):
                    time_str = datetime.fromtimestamp(match_time).strftime("%H:%M %d/%m")
                else:
                    time_str = str(match_time) if match_time else datetime.now().strftime("%H:%M %d/%m")

                # Format tiêu đề chuẩn: 🟢 [Giờ] ⚽ [Đội A] vs [Đội B] ([BLV])
                blv_str = f" ({commentator})" if commentator else ""
                title = f"🟢 {time_str} ⚽ {home} vs {away}{blv_str}"
                
                logo = match.get("home_logo") or match.get("logo") or ""
                
                # Lấy danh sách link phát sóng
                links = match.get("links") or match.get("play_urls") or []
                if not links and (match.get("play_url") or match.get("stream_url")):
                    links = [{"url": match.get("play_url") or match.get("stream_url"), "name": "HD"}]

                for idx, link in enumerate(links):
                    stream_url = link.get("url") or link.get("play_url") if isinstance(link, dict) else str(link)
                    if not stream_url or not stream_url.startswith("http"):
                        continue
                    
                    quality = link.get("name") if isinstance(link, dict) and link.get("name") else f"Link {idx+1}"
                    full_title = f"{title} [{quality}]"

                    matches.append({
                        "group": ep["group"],
                        "title": full_title,
                        "logo": logo,
                        "url": stream_url,
                        "referer": ep["referer"]
                    })
        except Exception as e:
            print(f"Lỗi khi cào dữ liệu từ {ep['group']}: {e}")

    return matches

def main():
    now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    print(f"⏳ Đang cập nhật danh sách IPTV lúc {now_str}...")

    m3u_content = [
        "#EXTM3U\n",
        f'#EXTINF:-1 group-title="HỆ THỐNG",🔄 Cập nhật hệ thống: {now_str}\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n"
    ]

    live_matches = parse_xoilac_matches()

    if not live_matches:
        print("⚠️ Không lấy được dữ liệu mới từ API. Kiểm tra lại kết nối mạng hoặc nguồn API.")
    else:
        for item in live_matches:
            logo_attr = f' tvg-logo="{item["logo"]}"' if item["logo"] else ""
            m3u_content.append(f'#EXTINF:-1{logo_attr} group-title="{item["group"]}",{item["title"]}\n')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={item["referer"]}\n')
            m3u_content.append(f'{item["url"]}\n')

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(m3u_content)

    print(f"✅ Hoàn tất! Đã ghi {len(live_matches)} trận đấu mới nhất vào playlist.m3u")

if __name__ == "__main__":
    main()