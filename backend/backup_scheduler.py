# Scheduled backup system for Media Basher
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from backup_manager import backup_manager
from notifications import notification_manager, NotificationType

logger = logging.getLogger(__name__)

class BackupScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, Dict] = {}
        self.scheduler.start()
        logger.info("Backup scheduler initialized")

    def add_schedule(self, schedule_id: str, cron_expression: str, backup_config: Dict):
        """Add a scheduled backup job"""
        try:
            # Parse cron expression (minute hour day month day_of_week)
            parts = cron_expression.split()
            if len(parts) != 5:
                raise ValueError("Invalid cron expression. Expected format: minute hour day month day_of_week")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create cron trigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            # Add job
            job = self.scheduler.add_job(
                self._execute_backup,
                trigger=trigger,
                args=[schedule_id, backup_config],
                id=schedule_id,
                replace_existing=True
            )
            
            self.jobs[schedule_id] = {
                "id": schedule_id,
                "cron": cron_expression,
                "backup_config": backup_config,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "enabled": True
            }
            
            logger.info(f"Backup schedule added: {schedule_id} with cron: {cron_expression}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add backup schedule: {e}")
            raise

    def remove_schedule(self, schedule_id: str):
        """Remove a scheduled backup job"""
        try:
            self.scheduler.remove_job(schedule_id)
            if schedule_id in self.jobs:
                del self.jobs[schedule_id]
            logger.info(f"Backup schedule removed: {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove backup schedule: {e}")
            return False

    def pause_schedule(self, schedule_id: str):
        """Pause a scheduled backup job"""
        try:
            self.scheduler.pause_job(schedule_id)
            if schedule_id in self.jobs:
                self.jobs[schedule_id]['enabled'] = False
            logger.info(f"Backup schedule paused: {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to pause backup schedule: {e}")
            return False

    def resume_schedule(self, schedule_id: str):
        """Resume a paused backup job"""
        try:
            self.scheduler.resume_job(schedule_id)
            if schedule_id in self.jobs:
                self.jobs[schedule_id]['enabled'] = True
            logger.info(f"Backup schedule resumed: {schedule_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to resume backup schedule: {e}")
            return False

    async def _execute_backup(self, schedule_id: str, backup_config: Dict):
        """Execute a scheduled backup"""
        logger.info(f"Executing scheduled backup: {schedule_id}")
        
        try:
            result = await backup_manager.create_backup(backup_config)
            
            if result.get('status') == 'completed':
                await notification_manager.send_notification(
                    title="Scheduled Backup Completed",
                    message=f"Backup {result.get('id')} created successfully (Schedule: {schedule_id})",
                    notification_type=NotificationType.SUCCESS,
                    channels=[],
                    config=None
                )
            else:
                await notification_manager.send_notification(
                    title="Scheduled Backup Failed",
                    message=f"Backup failed: {result.get('error', 'Unknown error')}",
                    notification_type=NotificationType.ERROR,
                    channels=[],
                    config=None
                )
        except Exception as e:
            logger.error(f"Scheduled backup execution failed: {e}")
            await notification_manager.send_notification(
                title="Scheduled Backup Error",
                message=f"Backup execution error: {str(e)}",
                notification_type=NotificationType.ERROR,
                channels=[],
                config=None
            )

    def get_schedules(self) -> List[Dict]:
        """Get all backup schedules"""
        result = []
        for schedule_id, job_info in self.jobs.items():
            # Get updated next run time
            try:
                job = self.scheduler.get_job(schedule_id)
                if job:
                    job_info['next_run'] = job.next_run_time.isoformat() if job.next_run_time else None
            except:
                pass
            result.append(job_info)
        return result

    def shutdown(self):
        """Shutdown the scheduler"""
        self.scheduler.shutdown()
        logger.info("Backup scheduler shut down")

backup_scheduler = BackupScheduler()