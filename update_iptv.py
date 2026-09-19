import json
import re
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"

def get_live_matches():
    now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    print(f"⏳ Bắt đầu cào luồng bóng đá trực tiếp lúc {now_str}...")
    
    m3u_lines = [
        "#EXTM3U\n",
        f'#EXTINF:-1 group-title="HỆ THỐNG",🔄 Cập nhật lần cuối: {now_str}\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n",
        '#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n',
        "http://cdn.vtvall.vn/vtv3/index.m3u8\n"
    ]

    # Các cổng API Mirror & Embed Server không bị chặn IP Cloudflare/DataCenter
    endpoints = [
        {
            "group": "Xôi Lạc TV",
            "url": "https://bitg.site/api/matches/live",
            "referer": "https://xoilac.com/"
        },
        {
            "group": "Bia Ôm TV",
            "url": "https://api.vebo.xyz/api/match/featured",
            "referer": "https://vebo.xyz/"
        },
        {
            "group": "Thập Cẩm TV",
            "url": "https://api.thapcam.net/api/v1/matches",
            "referer": "https://thapcam.net/"
        }
    ]

    total_added = 0
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "*/*",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
        "Origin": "https://google.com"
    }

    for ep in endpoints:
        try:
            res = requests.get(ep["url"], headers=headers, impersonate="chrome120", timeout=12)
            if res.status_code == 200:
                data = res.json()
                items = data.get("data") or data.get("matches") or (data if isinstance(data, list) else [])

                for item in items:
                    # Bóc tách tên đội, BLV, logo
                    home = item.get("home_name") or item.get("home", {}).get("name", "Đội nhà")
                    away = item.get("away_name") or item.get("away", {}).get("name", "Đội khách")
                    match_time = item.get("match_time") or item.get("time", "Đang đá")
                    blv = item.get("commentator") or item.get("blv", "")
                    logo = item.get("home_logo") or item.get("logo", "")

                    links = item.get("play_urls") or item.get("links") or []
                    for idx, link in enumerate(links):
                        stream_url = ""
                        server_name = f"Server {idx+1}"

                        if isinstance(link, dict):
                            stream_url = link.get("url") or link.get("link", "")
                            server_name = link.get("name") or server_name
                        elif isinstance(link, str):
                            stream_url = link

                        if stream_url and ("m3u8" in stream_url or "flv" in stream_url):
                            title = f"🟢 [{match_time}] {home} vs {away} - {server_name}"
                            if blv:
                                title += f" ({blv})"

                            logo_attr = f'tvg-logo="{logo}" ' if logo else ""
                            m3u_lines.append(f'#EXTINF:-1 {logo_attr}group-title="{ep["group"]}",{title}\n')
                            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                            m3u_lines.append(f'#EXTVLCOPT:http-referrer={ep["referer"]}\n')
                            m3u_lines.append(f"{stream_url}\n")
                            total_added += 1
        except Exception as e:
            print(f"⚠️ Bỏ qua {ep['group']}: {e}")

    # Kênh dự phòng cố định nếu thời điểm cào chưa có trận bóng nào đá
    if total_added == 0:
        print("ℹ️ Hiện tại không có trận đấu live, chèn luồng dự phòng...")
        backup_streams = [
            ("Vua Sân Cỏ TV", "🟢 20:45 ⚽ Arkadag FK vs Al-Muharraq (Tôn Quyền)", "https://cdn-global.ebaclofen.org/vsc/jonhny5/index.m3u8"),
            ("Bia Ôm TV", "02:00 ⚽ Liverpool vs Tottenham Hotspur [HLS]", "https://cdnhls.xbdbotv.live/live/MTk4NzI1NjE6dWppY2ViaXFnN2Fmazdhendla3Q3azE3Onp0cTFxZTZ5NDhtbGNiczB0cmFoc3dpbQ/index.m3u8"),
            ("Xôi Lạc Z TV", "02:00 ⚽ Ipswich Town vs Arsenal (HD NICK)", "https://live2.domaincdn.cc/livecdn/channel-5.flv")
        ]
        for group, title, url in backup_streams:
            m3u_lines.append(f'#EXTINF:-1 group-title="{group}",{title}\n')
            m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
            m3u_lines.append(f"{url}\n")

    print(f"✅ Đã thêm tổng cộng {total_added if total_added > 0 else len(backup_streams)} luồng phát.")
    return m3u_lines

def main():
    lines = get_live_matches()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("🎉 Hoàn tất ghi playlist.m3u!")

if __name__ == "__main__":
    main()