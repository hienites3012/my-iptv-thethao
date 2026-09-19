import re
import json
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"

def fetch_live_streams():
    print("⏳ Đang quét trực tiếp các trang web bóng đá live...")
    
    m3u_lines = ["#EXTM3U\n"]
    
    # Kênh Test cố định
    m3u_lines.append('#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n')
    m3u_lines.append("http://cdn.vtvall.vn/vtv3/index.m3u8\n")

    # Danh sách các web bóng đá trực tiếp Việt Nam hiện hành
    sources = [
        {"name": "Xôi Lạc TV", "url": "https://xoilac365.tv", "referer": "https://xoilac365.tv/"},
        {"name": "Bia Ôm TV", "url": "https://xbdbotv.live", "referer": "https://xbdbotv.live/"},
        {"name": "Thập Cẩm TV", "url": "https://thapcam.net", "referer": "https://thapcam.net/"}
    ]

    total_channels = 0

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    for src in sources:
        try:
            # Giả lập Chrome vượt WAF/Cloudflare để tải HTML gốc
            res = requests.get(src["url"], headers=headers, impersonate="chrome120", timeout=10)
            if res.status_code == 200:
                html = res.text
                
                # Tìm các chuỗi JSON chứa thông tin trận đấu nhúng trong code JS của trang web
                json_matches = re.findall(r'window\.__DATA__\s*=\s*(\{.*?\});', html) or \
                               re.findall(r'var\s+matches\s*=\s*(\[.*?\]);', html) or \
                               re.findall(r'__NEXT_DATA__"\s*type="application/json">(\{.*?\})</script>', html)

                if json_matches:
                    for raw_json in json_matches:
                        try:
                            data = json.loads(raw_json)
                            # Bóc tách dữ liệu nếu là Next.js data structure
                            if "props" in data:
                                data = data.get("props", {}).get("pageProps", {}).get("matches", [])
                            
                            if isinstance(data, list):
                                for item in data:
                                    home = item.get("home_name") or item.get("homeTeam", {}).get("name", "Đội nhà")
                                    away = item.get("away_name") or item.get("awayTeam", {}).get("name", "Đội khách")
                                    time_str = item.get("match_time") or item.get("time", "Live")
                                    blv = item.get("commentator") or item.get("blv", "")
                                    logo = item.get("home_logo") or item.get("logo", "")
                                    
                                    links = item.get("links") or item.get("play_urls") or []
                                    for idx, l in enumerate(links):
                                        url_stream = l.get("url") if isinstance(l, dict) else l
                                        server = l.get("name", f"Server {idx+1}") if isinstance(l, dict) else f"Server {idx+1}"
                                        
                                        if url_stream and ("m3u8" in url_stream or "flv" in url_stream):
                                            title = f"🟢 [{time_str}] {home} vs {away} - {server}"
                                            if blv:
                                                title += f" ({blv})"
                                                
                                            logo_attr = f'tvg-logo="{logo}" ' if logo else ""
                                            m3u_lines.append(f'#EXTINF:-1 {logo_attr}group-title="{src["name"]}",{title}\n')
                                            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                                            m3u_lines.append(f'#EXTVLCOPT:http-referrer={src["referer"]}\n')
                                            m3u_lines.append(f"{url_stream}\n")
                                            total_channels += 1
                        except Exception:
                            continue

                # Phương án 2: Quét Regex trực tiếp các URL Stream .m3u8 / .flv nằm trong HTML
                if total_channels == 0:
                    stream_urls = re.findall(r'https?://[^\s\'"]+\.(?:m3u8|flv)[^\s\'"]*', html)
                    stream_urls = list(set(stream_urls)) # Lọc trùng
                    
                    for idx, url_stream in enumerate(stream_urls):
                        m3u_lines.append(f'#EXTINF:-1 group-title="{src["name"]}",🟢 Luồng trực tiếp {idx+1}\n')
                        m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                        m3u_lines.append(f'#EXTVLCOPT:http-referrer={src["referer"]}\n')
                        m3u_lines.append(f"{url_stream}\n")
                        total_channels += 1

        except Exception as e:
            print(f"⚠️ Lỗi quét {src['name']}: {e}")

    print(f"✅ Bóc tách thành công {total_channels} luồng phát bóng đá.")
    return m3u_lines

def main():
    lines = fetch_live_streams()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🎉 Hoàn tất cập nhật playlist.m3u lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if __name__ == "__main__":
    main()