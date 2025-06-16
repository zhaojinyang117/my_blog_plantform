import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags
import threading


def generate_verification_token():
    """生成验证token"""
    return secrets.token_urlsafe(32)


def send_verification_email(user):
    """异步发送验证邮件"""

    def _send_email():
        # 内部函数，用于在单独线程中发送邮件
        try:
            # 生成验证token
            token = generate_verification_token()
            user.email_verification_token = token
            user.save(update_fields=["email_verification_token"])

            # 构建验证链接
            frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:3000")
            verification_url = f"{frontend_url}/verify-email?token={token}"

            # 邮件内容
            subject = "邮箱验证"
            html_message = f"""
            <h2>欢迎注册博客平台！</h2>
            <p>您好 {user.username}，</p>
            <p>感谢您注册我们的博客平台。请点击下面的链接完成邮箱验证：</p>
            <p><a href="{verification_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">验证邮箱</a></p>
            <p>或复制以下链接到浏览器：</p>
            <p>{verification_url}</p>
            <p>此链接24小时内有效。</p>
            <p>如果您没有注册账户，请忽略此邮件。</p>
            """

            # 将HTML内容转换为纯文本格式，用于不支持HTML的邮件客户端
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,  # 邮件主题
                message=plain_message,  # 纯文本邮件内容
                from_email=settings.DEFAULT_FROM_EMAIL,  # 发件人邮箱地址
                recipient_list=[user.email],  # 收件人邮箱列表
                html_message=html_message,  # HTML格式的邮件内容
                fail_silently=False,  # 不静默失败，抛出异常便于调试
            )

            print(f"验证邮件已发送至 {user.email}")
        except Exception as e:
            print(f"发送验证邮件失败: {e}")

    # 在后台线程中执行发送邮件
    email_thread = threading.Thread(target=_send_email)
    # 设置为守护线程，当主程序退出时，该线程会自动结束
    # 避免主程序结束时还有邮件发送线程在后台运行
    email_thread.daemon = True
    email_thread.start()


##########################
#   重置密码邮件先pass     #
##########################