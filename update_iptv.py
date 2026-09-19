import re
from datetime import datetime
from curl_cffi import requests

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36"

def fetch_live_m3u():
    print("⏳ Đang cào trực tiếp danh sách trận đấu và token phát sóng...")
    
    m3u_lines = ["#EXTM3U\n"]
    m3u_lines.append('#EXTINF:-1 group-title="KÊNH TEST",🟢 Kênh Test IPTV (VTV3 HD)\n')
    m3u_lines.append("http://cdn.vtvall.vn/vtv3/index.m3u8\n")

    # Danh sách các server API xuất danh sách trận chứa token chuẩn
    targets = [
        {
            "group": "Vua Sân Cỏ TV",
            "url": "https://api.vsc.ebaclofen.org/api/matches/live",
            "referer": "https://vuasanco.com/"
        },
        {
            "group": "Bia Ôm TV",
            "url": "https://api.xbdbotv.live/api/v1/match/live-streams",
            "referer": "https://xbdbotv.live/"
        },
        {
            "group": "Xôi Lạc Z TV",
            "url": "https://api.zundrixmediapipeline.com/api/v1/live",
            "referer": "https://xoilac.com/"
        },
        {
            "group": "Chuối Chiên TV",
            "url": "https://media.chuoichientv.net/api/v1/streams",
            "referer": "https://chuoichientv.net/"
        }
    ]

    total_added = 0

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://google.com"
    }

    for target in targets:
        try:
            res = requests.get(target["url"], headers=headers, impersonate="chrome120", timeout=10)
            if res.status_code == 200:
                # Quét trực tiếp định dạng M3U8/FLV kèm full token bảo mật từ JSON trả về
                raw_text = res.text
                
                # Tìm tất cả các đoạn link chứa cdn stream kèm token mã hóa
                matches = re.findall(r'(https?://[^\s\'"]+\.(?:m3u8|flv)\?[^\s\'"]*|https?://[^\s\'"]+\.(?:m3u8|flv))', raw_text)
                
                # Lọc link trùng lặp
                unique_urls = list(dict.fromkeys(matches))

                for idx, stream_url in enumerate(unique_urls):
                    title = f"🟢 Trận Live {idx+1} - [{target['group']}]"
                    
                    m3u_lines.append(f'#EXTINF:-1 group-title="{target["group"]}",{title}\n')
                    m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}\n')
                    m3u_lines.append(f'#EXTVLCOPT:http-referrer={target["referer"]}\n')
                    m3u_lines.append(f"{stream_url}\n")
                    total_added += 1

        except Exception as e:
            print(f"⚠️ Không thể lấy luồng từ {target['group']}: {e}")

    print(f"✅ Đã trích xuất thành công {total_added} link live chứa Token chuẩn.")
    return m3u_lines

def main():
    lines = fetch_live_m3u()
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"🎉 Cập nhật hoàn tất lúc {datetime.now().strftime('%H:%M %d/%m/%Y')}")

if __name__ == "__main__":
    main()