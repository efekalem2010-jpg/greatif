
import http.server
import socketserver
import json
import urllib.request
import re

PORT = 5000

# --- WEB SİTESİ ARAYÜZÜ (HTML + CSS + JS) ---
HTML_PAGE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GREATIF SCRAPING</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #1e1e2f; color: #ffffff; margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .container { background-color: #2a2a40; padding: 30px; border-radius: 12px; box-shadow: 0 8px 20px rgba(0,0,0,0.3); width: 90%; max-width: 500px; text-align: center; }
        h1 { color: #00ffcc; margin-bottom: 20px; letter-spacing: 2px; font-size: 24px; }
        .hidden { display: none !important; }
        input { width: 90%; padding: 12px; margin: 10px 0; border: none; border-radius: 6px; background-color: #3f3f5a; color: white; outline: none; }
        button { width: 95%; padding: 12px; margin-top: 15px; border: none; border-radius: 6px; background-color: #00ffcc; color: #1e1e2f; font-weight: bold; font-size: 16px; cursor: pointer; }
        button:hover { background-color: #00cca3; }
        .tabs { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .tab-btn { width: 32%; background-color: #3f3f5a; color: white; margin-top: 0; padding: 10px 0; font-size: 14px;}
        .tab-btn.active { background-color: #ff007f; color: white; }
        .result-box { margin-top: 20px; padding: 15px; background-color: #1e1e2f; border-radius: 8px; text-align: left; border: 1px solid #3f3f5a; }
        .result-box p { margin: 8px 0; font-size: 15px; }
        .highlight { color: #00ffcc; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container" id="authSection">
        <h1>GREATIF SCRAPING</h1>
        <p>Sisteme erişmek için giriş yapın.</p>
        <input type="text" id="username" placeholder="Kullanıcı Adı">
        <input type="password" id="password" placeholder="Şifre">
        <button onclick="login()">Giriş Yap</button>
    </div>

    <div class="container hidden" id="appSection">
        <h1>GREATIF SCRAPING</h1>
        <div class="tabs">
            <button class="tab-btn active" onclick="changeTab('Instagram', this)">Instagram</button>
            <button class="tab-btn" onclick="changeTab('TikTok', this)">TikTok</button>
            <button class="tab-btn" onclick="changeTab('X (Twitter)', this)">X</button>
        </div>
        <h3 id="platformTitle" style="font-size: 16px;">Instagram Linki Giriniz</h3>
        <input type="text" id="postUrl" placeholder="Gönderi linkini yapıştırın...">
        <button onclick="fetchData()" id="fetchBtn">Verileri Analiz Et</button>

        <div class="result-box hidden" id="resultBox">
            <p>Platform: <span class="highlight" id="resPlatform">-</span></p>
            <p>Hesap İsmi: <span class="highlight" id="resAccount">-</span></p>
            <p>İzlenme: <span class="highlight" id="resViews">-</span></p>
            <p>Beğeni: <span class="highlight" id="resLikes">-</span></p>
            <p>Yorum: <span class="highlight" id="resComments">-</span></p>
            <p>Kaydetme: <span class="highlight" id="resSaves">-</span></p>
        </div>
    </div>

    <script>
        let currentPlatform = 'Instagram';

        function login() {
            if(document.getElementById('username').value !== "" && document.getElementById('password').value !== "") {
                document.getElementById('authSection').classList.add('hidden');
                document.getElementById('appSection').classList.remove('hidden');
            } else { alert("Lütfen bilgileri doldurun."); }
        }

        function changeTab(platform, element) {
            currentPlatform = platform;
            document.getElementById('platformTitle').innerText = platform + " Linki Giriniz";
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            element.classList.add('active');
            document.getElementById('resultBox').classList.add('hidden');
            document.getElementById('postUrl').value = "";
        }

        async function fetchData() {
            const url = document.getElementById('postUrl').value;
            const btn = document.getElementById('fetchBtn');
            if(url === "") { alert("Lütfen bir link giriniz."); return; }

            btn.innerText = "Veriler Çekiliyor... Lütfen Bekleyin";
            btn.disabled = true;

            try {
                const response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ platform: currentPlatform, url: url })
                });

                const data = await response.json();

                if(data.error) {
                    alert(data.error);
                } else {
                    document.getElementById('resultBox').classList.remove('hidden');
                    document.getElementById('resPlatform').innerText = data.platform;
                    document.getElementById('resAccount').innerText = data.accountName;
                    document.getElementById('resViews').innerText = data.views;
                    document.getElementById('resLikes').innerText = data.likes;
                    document.getElementById('resComments').innerText = data.comments;
                    document.getElementById('resSaves').innerText = data.saves;
                }
            } catch (error) {
                alert("Veri çekilemedi. Bağlantıyı kontrol edin.");
            }
            btn.innerText = "Verileri Analiz Et";
            btn.disabled = false;
        }
    </script>
</body>
</html>
"""

# --- GÖMÜLÜ SUNUCU VE KAZIMA (SCRAPING) MOTORU ---
class ScrapingHandler(http.server.SimpleHTTPRequestHandler):
    
    # HTML sayfasını ekrana basan bölüm
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    # Veri kazıma isteğini karşılayan bölüm
    def do_POST(self):
        if self.path == '/api/scrape':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            platform = data.get('platform')
            url = data.get('url')

            if not url:
                self._send_json({"error": "Link boş olamaz"}, 400)
                return

            result = {
                "platform": platform,
                "accountName": "Bilinmiyor",
                "views": "Veri Yok",
                "likes": "Veri Yok",
                "comments": "Veri Yok",
                "saves": "Veri Yok"
            }

            headers = {
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
            }

            try:
                if platform == 'X (Twitter)':
                    tweet_id_match = re.search(r'status/(\d+)', url)
                    if tweet_id_match:
                        tweet_id = tweet_id_match.group(1)
                        api_url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}"
                        req = urllib.request.Request(api_url, headers=headers)
                        with urllib.request.urlopen(req, timeout=10) as response:
                            tweet_data = json.loads(response.read().decode('utf-8'))
                            result["accountName"] = "@" + tweet_data.get("user", {}).get("screen_name", "Bulunamadı")
                            result["views"] = tweet_data.get("views", {}).get("count", "Gizli")
                            result["likes"] = str(tweet_data.get("favorite_count", 0))
                            result["comments"] = str(tweet_data.get("reply_count", 0))
                    else:
                        self._send_json({"error": "Geçerli bir X (Twitter) gönderi linki değil."}, 400)
                        return

                elif platform in ['Instagram', 'TikTok']:
                    req = urllib.request.Request(url, headers=headers)
                    with urllib.request.urlopen(req, timeout=10) as response:
                        html = response.read().decode('utf-8')
                        
                        meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', html, re.IGNORECASE)
                        
                        if meta_match:
                            desc = meta_match.group(1)
                            likes_match = re.search(r'([\d,\.]+)\s+Likes', desc, re.IGNORECASE)
                            comments_match = re.search(r'([\d,\.]+)\s+Comments', desc, re.IGNORECASE)
                            
                            if platform == 'Instagram':
                                user_match = re.search(r'\(@([a-zA-Z0-9_\.]+)\)', desc)
                                if user_match: result["accountName"] = "@" + user_match.group(1)
                                
                            elif platform == 'TikTok':
                                views_match = re.search(r'([\d,\.]+)\s+Views', desc, re.IGNORECASE)
                                if views_match: result["views"] = views_match.group(1)
                                
                                title_match = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
                                if title_match and '(@' in title_match.group(1):
                                    result["accountName"] = "@" + title_match.group(1).split('(@')[1].split(')')[0]

                            if likes_match: result["likes"] = likes_match.group(1)
                            if comments_match: result["comments"] = comments_match.group(1)
                        else:
                             self._send_json({"error": f"{platform} bot koruması veriyi engelledi."}, 400)
                             return

                self._send_json(result, 200)

            except Exception as e:
                self._send_json({"error": f"Bir hata oluştu: {str(e)}"}, 500)

    # Veriyi JSON olarak döndüren yardımcı fonksiyon
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

# Sunucuyu başlatma
if __name__ == '__main__':
    # Adres çakışmalarını önlemek için allow_reuse_address ekliyoruz
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ScrapingHandler) as httpd:
        print("--------------------------------------------------")
        print("Sistem Hazır! Lütfen arka planda açık bırakıp Safari'ye geçin:")
        print(f"http://127.0.0.1:{PORT}")
        print("--------------------------------------------------")
        httpd.serve_forever()
