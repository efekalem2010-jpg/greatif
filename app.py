import http.server
import socketserver
import json
import urllib.parse
import yt_dlp

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

# --- GÖMÜLÜ SUNUCU VE YT-DLP GÜÇLENDİRİLMİŞ MOTORU ---
class ScrapingHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

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

            try:
                # yt-dlp ile bot korumalarını bypass ederek verileri çekiyoruz
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': False,
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    if info:
                        # Hesap / Uploader Adı
                        uploader = info.get('uploader') or info.get('creator') or info.get('channel')
                        if uploader:
                            result["accountName"] = "@" + uploader.replace("@", "")

                        # Beğeni Sayısı
                        likes = info.get('like_count')
                        if likes is not None:
                            result["likes"] = f"{likes:,}"

                        # Yorum Sayısı
                        comments = info.get('comment_count')
                        if comments is not None:
                            result["comments"] = f"{comments:,}"

                        # İzlenme Sayısı
                        views = info.get('view_count')
                        if views is not None:
                            result["views"] = f"{views:,}"
                        
                        # Eğer hiçbir istatistik dönmediyse
                        if result["likes"] == "Veri Yok" and result["views"] == "Veri Yok":
                            result["likes"] = "Mevcut Değil"
                            result["views"] = "Mevcut Değil"

                self._send_json(result, 200)

            except Exception as e:
                self._send_json({"error": f"Bot koruması aşılamadı veya geçersiz link: {str(e)}"}, 500)

    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ScrapingHandler) as httpd:
        httpd.serve_forever()
