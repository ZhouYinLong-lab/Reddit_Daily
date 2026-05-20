import os
import datetime
import base64
from io import BytesIO
import praw
import qrcode
import requests
from weasyprint import HTML

# ==========================================
# 1. 配置与环境变量读取
# ==========================================
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USERNAME = os.getenv("REDDIT_USERNAME", "YOUR_REDDIT_USERNAME") # 替换为你的 Reddit ID
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# 订阅者列表（实际项目中可以从数据库或 CSV 读取）
# 环境变量传入格式：email1@example.com,email2@example.com
SUBSCRIBERS = os.getenv("SUBSCRIBERS", "your_test_email@example.com").split(",") 
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "newsletter@yourdomain.com") # 你的发件邮箱

# ==========================================
# 2. 数据获取与处理
# ==========================================
def fetch_reddit_posts(username, limit=10):
    print(f"Fetching posts for user: {username}...")
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent="script:personal-newsletter-generator:v1.0"
    )
    
    posts = []
    # 获取用户最近发出的热帖
    for submission in reddit.redditor(username).submissions.new(limit=limit):
        # 截取摘要，优先使用正文，如果没有正文则留白
        summary_text = submission.selftext[:250] + "..." if submission.selftext else "Click the QR code to view the full discussion and link."
        
        posts.append({
            "title": submission.title,
            "meta": f"r/{submission.subreddit.display_name} • {submission.score} Upvotes",
            "url": f"https://www.reddit.com{submission.permalink}",
            "summary": summary_text
        })
    return posts

def generate_qr_base64(url):
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

# ==========================================
# 3. HTML 排版生成
# ==========================================
def generate_newsletter_html(posts):
    current_date = datetime.datetime.now().strftime("%B %Y")
    issue_number = datetime.datetime.now().strftime("%V") # 使用周数作为期号
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    @page {{
        size: A4;
        margin: 15mm 12mm 18mm 12mm;
        background-color: #fdfcf9;
        @bottom-right {{
            content: "Page " counter(page);
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            font-size: 8pt; color: #777777;
        }}
        @bottom-left {{
            content: "Reddit Tech Digest • Distributed Static File Edition";
            font-family: -apple-system, BlinkMacSystemFont, Arial, sans-serif;
            font-size: 8pt; color: #777777; font-weight: bold;
        }}
    }}
    body {{
        margin: 0; padding: 0;
        font-family: "Georgia", "Times New Roman", serif;
        color: #1a1a1a; font-size: 9pt; line-height: 1.4;
    }}
    .header-container {{
        width: 100%; border-bottom: 3px double #111111;
        padding-bottom: 8px; margin-bottom: 15px; text-align: center;
    }}
    .header-title {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 26pt; font-weight: 900; margin: 0 0 4px 0;
        text-transform: uppercase; color: #111111;
    }}
    .header-meta-table {{
        display: table; width: 100%;
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 8.5pt; color: #444444; border-top: 1px solid #111111;
        padding-top: 4px; margin-top: 5px; text-transform: uppercase;
    }}
    .meta-cell {{ display: table-cell; }}
    .meta-left {{ text-align: left; width: 33%; }}
    .meta-center {{ text-align: center; width: 34%; font-weight: bold; color: #c62828; }}
    .meta-right {{ text-align: right; width: 33%; }}
    .columns-wrapper {{
        column-count: 3; column-gap: 8mm; column-rule: 0.5pt solid #dddddd;
    }}
    .post-item {{
        break-inside: avoid; margin-bottom: 10mm;
        padding-bottom: 6mm; border-bottom: 0.5pt dashed #b5b5b5;
    }}
    .post-item:last-child {{ border-bottom: none; }}
    .post-title {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-weight: bold; font-size: 10.5pt; line-height: 1.25;
        margin: 0 0 4px 0; color: #000000;
    }}
    .post-meta {{
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 7.5pt; color: #666666; margin-bottom: 6px;
    }}
    .qr-box {{
        float: right; width: 44pt; height: 44pt;
        margin-left: 8px; margin-bottom: 2px;
        border: 1px solid #e0e0e0; padding: 2px; background: #ffffff;
    }}
    .qr-box img {{ width: 100%; height: 100%; display: block; }}
    .post-summary {{ text-align: justify; margin: 0; color: #222222; }}
    </style>
    </head>
    <body>
    <div class="header-container">
        <div class="header-title">Reddit 技术热帖简报</div>
        <div class="header-meta-table">
            <div class="meta-cell meta-left">Issue No. W{issue_number}</div>
            <div class="meta-cell meta-center">Personal Tech Digest</div>
            <div class="meta-cell meta-right">{current_date}</div>
        </div>
    </div>
    <div class="columns-wrapper">
    """
    
    for post in posts:
        qr_b64 = generate_qr_base64(post['url'])
        html_content += f"""
        <div class="post-item">
            <div class="post-title">{post['title']}</div>
            <div class="post-meta">{post['meta']}</div>
            <div class="post-summary">
                <div class="qr-box">
                    <img src="data:image/png;base64,{qr_b64}" alt="QR">
                </div>
                {post['summary']}
            </div>
        </div>
        """
        
    html_content += "</div></body></html>"
    return html_content

# ==========================================
# 4. 邮件分发 (通过 Resend API)
# ==========================================
def send_email_with_pdf(pdf_path, subscribers):
    print("Preparing to send emails...")
    
    # 将 PDF 转为 Base64 以供 API 上传附件
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.b64encode(f.read()).decode("utf-8")
        
    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "from": f"Tech Digest <{SENDER_EMAIL}>",
        "to": subscribers,
        "subject": f"你的每周 Reddit 技术简报已送达！ ({datetime.datetime.now().strftime('%Y-%m-%d')})",
        "html": "<p>你好，</p><p>本周的 Reddit 个人技术热帖简报已生成，请查收附件 PDF 文件。使用手机扫描附件中的二维码即可直接跳转原帖参与讨论。</p><p>祝阅读愉快！</p>",
        "attachments": [
            {
                "filename": "Weekly_Reddit_Digest.pdf",
                "content": pdf_b64
            }
        ]
    }
    
    response = requests.post("https://api.resend.com/emails", headers=headers, json=payload)
    if response.status_code in [200, 201]:
        print("Email sent successfully to:", subscribers)
    else:
        print(f"Failed to send email. Status: {response.status_code}, Response: {response.text}")

# ==========================================
# 5. 主执行流程
# ==========================================
if __name__ == "__main__":
    print("=== Starting Newsletter Generation Pipeline ===")
    
    # 1. 获取数据
    posts_data = fetch_reddit_posts(REDDIT_USERNAME, limit=12)
    if not posts_data:
        print("No posts found. Exiting.")
        exit()
        
    # 2. 生成 HTML
    print("Generating HTML layout...")
    final_html = generate_newsletter_html(posts_data)
    
    # 3. 渲染为 PDF
    pdf_filename = "newsletter_output.pdf"
    print(f"Rendering PDF to {pdf_filename}...")
    HTML(string=final_html).write_pdf(pdf_filename)
    
    # 4. 发送邮件
    send_email_with_pdf(pdf_filename, SUBSCRIBERS)
    
    print("=== Pipeline Completed Successfully ===")