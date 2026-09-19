import json
from datetime import datetime
from curl_cffi import requests

def fetch_football_matches():
    print("⏳ Đang cào danh sách trận đấu bóng đá từ Server Quốc tế...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
        "Referer": "https://xoilac.com/",
        "Accept": "application/json, text/plain, */*"
    }

    # API nguồn bóng đá thực tế
    api_urls = [
        "https://api.xoilac.live/api/match/featured",
        "https://api.v2.xoilac.tv/api/match/featured"
    ]

    m3u_lines = ["#EXTM3U\n"]
    match_count = 0

    for url in api_urls:
        try:
            response = requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
            if response.status_code == 200:
                data = response.json()
                matches = data.get("data", []) if isinstance(data, dict) else data

                for match in matches:
                    home = match.get("home_name") or match.get("home", {}).get("name", "Đội nhà")
                    away = match.get("away_name") or match.get("away", {}).get("name", "Đội khách")
                    time_str = match.get("match_time") or match.get("time", "Đang đá")
                    blv = match.get("commentator") or match.get("blv", "BLV")
                    
                    is_live = match.get("is_live", False)
                    status = "🟢 LIVE" if is_live else "⏰"

                    links = match.get("play_urls") or match.get("links", [])
                    for idx, item in enumerate(links):
                        stream_url = item.get("url") if isinstance(item, dict) else item
                        server = item.get("name", f"Server {idx+1}") if isinstance(item, dict) else f"Server {idx+1}"
                        
                        if stream_url:
                            extinf = f'#EXTINF:-1 group-title="Bóng Đá Trực Tiếp",{status} [{time_str}] {home} vs {away} - {server} ({blv})\n'
                            m3u_lines.append(extinf)
                            m3u_lines.append(f"{stream_url}\n")
                            match_count += 1
                
                if match_count > 0:
                    print(f"✅ Tìm thấy {match_count} luồng phát bóng đá!")
                    break
        except Exception as e:
            print(f"⚠️ Nguồn {url} gặp lỗi: {e}")

    return m3u_lines

def main():
    lines = fetch_football_matches()
    if len(lines) > 1:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"🎉 Hoàn tất cào dữ liệu lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")
    else:
        print("❌ Thất bại: Không lấy được trận nào.")

if __name__ == "__main__":
    main()