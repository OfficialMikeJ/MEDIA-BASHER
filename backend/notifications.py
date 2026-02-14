from typing import Optional, Dict, List
from datetime import datetime, timezone
from enum import Enum
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import httpx

logger = logging.getLogger(__name__)

class NotificationType(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"

class NotificationChannel(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"
    DISCORD = "discord"
    SLACK = "slack"

class NotificationManager:
    def __init__(self):
        self.notifications: List[Dict] = []

    async def send_notification(
        self,
        title: str,
        message: str,
        notification_type: NotificationType,
        channels: List[NotificationChannel],
        config: Optional[Dict] = None
    ):
        notification = {
            "id": str(len(self.notifications) + 1),
            "title": title,
            "message": message,
            "type": notification_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "read": False
        }
        
        self.notifications.insert(0, notification)
        
        # Keep only last 100 notifications
        if len(self.notifications) > 100:
            self.notifications = self.notifications[:100]

        if config:
            for channel in channels:
                try:
                    if channel == NotificationChannel.EMAIL:
                        await self._send_email(title, message, config)
                    elif channel == NotificationChannel.WEBHOOK:
                        await self._send_webhook(title, message, notification_type, config)
                    elif channel == NotificationChannel.DISCORD:
                        await self._send_discord(title, message, notification_type, config)
                    elif channel == NotificationChannel.SLACK:
                        await self._send_slack(title, message, notification_type, config)
                except Exception as e:
                    logger.error(f"Failed to send {channel} notification: {e}")

        return notification

    async def _send_email(self, title: str, message: str, config: Dict):
        if not config.get('email_enabled'):
            return

        msg = MIMEMultipart()
        msg['From'] = config['email_from']
        msg['To'] = config['email_to']
        msg['Subject'] = f"[Media Basher] {title}"
        msg.attach(MIMEText(message, 'plain'))

        with smtplib.SMTP(config['smtp_host'], config['smtp_port']) as server:
            if config.get('smtp_use_tls'):
                server.starttls()
            if config.get('smtp_username'):
                server.login(config['smtp_username'], config['smtp_password'])
            server.send_message(msg)

    async def _send_webhook(self, title: str, message: str, notification_type: NotificationType, config: Dict):
        if not config.get('webhook_url'):
            return

        async with httpx.AsyncClient() as client:
            await client.post(
                config['webhook_url'],
                json={
                    "title": title,
                    "message": message,
                    "type": notification_type,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                timeout=10
            )

    async def _send_discord(self, title: str, message: str, notification_type: NotificationType, config: Dict):
        if not config.get('discord_webhook_url'):
            return

        color_map = {
            NotificationType.INFO: 0x3498db,
            NotificationType.SUCCESS: 0x10b981,
            NotificationType.WARNING: 0xf59e0b,
            NotificationType.ERROR: 0xef4444
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                config['discord_webhook_url'],
                json={
                    "embeds": [{
                        "title": title,
                        "description": message,
                        "color": color_map.get(notification_type, 0x3498db),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }]
                },
                timeout=10
            )

    async def _send_slack(self, title: str, message: str, notification_type: NotificationType, config: Dict):
        if not config.get('slack_webhook_url'):
            return

        color_map = {
            NotificationType.INFO: "#3498db",
            NotificationType.SUCCESS: "#10b981",
            NotificationType.WARNING: "#f59e0b",
            NotificationType.ERROR: "#ef4444"
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                config['slack_webhook_url'],
                json={
                    "attachments": [{
                        "color": color_map.get(notification_type, "#3498db"),
                        "title": title,
                        "text": message,
                        "ts": int(datetime.now(timezone.utc).timestamp())
                    }]
                },
                timeout=10
            )

    def get_notifications(self, limit: int = 50) -> List[Dict]:
        return self.notifications[:limit]

    def mark_as_read(self, notification_id: str):
        for notif in self.notifications:
            if notif['id'] == notification_id:
                notif['read'] = True
                break

    def mark_all_as_read(self):
        for notif in self.notifications:
            notif['read'] = False

notification_manager = NotificationManager()