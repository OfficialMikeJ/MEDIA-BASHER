# Alert management system for Media Basher
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import psutil
import logging
from notifications import notification_manager, NotificationType, NotificationChannel

logger = logging.getLogger(__name__)

class AlertRule:
    def __init__(self, rule_id: str, name: str, metric: str, threshold: float, comparison: str, enabled: bool = True):
        self.id = rule_id
        self.name = name
        self.metric = metric  # cpu, ram, disk
        self.threshold = threshold
        self.comparison = comparison  # gt (greater than), lt (less than)
        self.enabled = enabled
        self.last_triggered = None
        self.cooldown_minutes = 15  # Don't spam alerts

    def should_trigger(self, current_value: float) -> bool:
        if not self.enabled:
            return False
        
        # Check cooldown
        if self.last_triggered:
            cooldown = datetime.now(timezone.utc) - self.last_triggered
            if cooldown < timedelta(minutes=self.cooldown_minutes):
                return False
        
        # Check threshold
        if self.comparison == 'gt':
            return current_value > self.threshold
        elif self.comparison == 'lt':
            return current_value < self.threshold
        return False

class AlertManager:
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.is_monitoring = False
        self.notification_config = {}

    def add_rule(self, rule: AlertRule):
        self.rules.append(rule)
        logger.info(f"Alert rule added: {rule.name}")

    def remove_rule(self, rule_id: str):
        self.rules = [r for r in self.rules if r.id != rule_id]
        logger.info(f"Alert rule removed: {rule_id}")

    def update_rule(self, rule_id: str, updates: Dict):
        for rule in self.rules:
            if rule.id == rule_id:
                for key, value in updates.items():
                    setattr(rule, key, value)
                logger.info(f"Alert rule updated: {rule_id}")
                break

    def set_notification_config(self, config: Dict):
        self.notification_config = config

    async def start_monitoring(self):
        """Start monitoring and checking alert rules"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        logger.info("Alert monitoring started")
        
        while self.is_monitoring:
            try:
                await self.check_alerts()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in alert monitoring: {e}")
                await asyncio.sleep(60)

    def stop_monitoring(self):
        self.is_monitoring = False
        logger.info("Alert monitoring stopped")

    async def check_alerts(self):
        """Check all alert rules against current metrics"""
        try:
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            metrics = {
                'cpu': cpu_percent,
                'ram': ram.percent,
                'disk': disk.percent
            }
            
            # Check each rule
            for rule in self.rules:
                if rule.metric in metrics:
                    current_value = metrics[rule.metric]
                    
                    if rule.should_trigger(current_value):
                        await self.trigger_alert(rule, current_value)
                        rule.last_triggered = datetime.now(timezone.utc)
        
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")

    async def trigger_alert(self, rule: AlertRule, current_value: float):
        """Trigger an alert notification"""
        title = f"Alert: {rule.name}"
        message = f"{rule.metric.upper()} is {current_value:.1f}% (threshold: {rule.threshold}%)"
        
        # Send to notification system
        channels = []
        if self.notification_config.get('email_enabled'):
            channels.append(NotificationChannel.EMAIL)
        if self.notification_config.get('webhook_url'):
            channels.append(NotificationChannel.WEBHOOK)
        if self.notification_config.get('discord_webhook_url'):
            channels.append(NotificationChannel.DISCORD)
        if self.notification_config.get('slack_webhook_url'):
            channels.append(NotificationChannel.SLACK)
        
        await notification_manager.send_notification(
            title=title,
            message=message,
            notification_type=NotificationType.WARNING,
            channels=channels,
            config=self.notification_config
        )
        
        logger.warning(f"Alert triggered: {rule.name} - {message}")

    def get_rules(self) -> List[Dict]:
        """Get all alert rules"""
        return [{
            "id": rule.id,
            "name": rule.name,
            "metric": rule.metric,
            "threshold": rule.threshold,
            "comparison": rule.comparison,
            "enabled": rule.enabled,
            "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
        } for rule in self.rules]

alert_manager = AlertManager()