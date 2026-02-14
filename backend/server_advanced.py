# Advanced features extension for Media Basher
# This file contains additional routes for advanced features

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File, BackgroundTasks
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
import docker
import asyncio
import yaml
import os
from websocket_manager import manager
from notifications import notification_manager, NotificationType, NotificationChannel
from metrics_collector import metrics_collector
from backup_manager import backup_manager

advanced_router = APIRouter(prefix="/api/advanced")

# ============ MODELS ============

class ResourceLimits(BaseModel):
    cpu_limit: Optional[float] = None  # CPU cores (e.g., 1.5)
    memory_limit: Optional[str] = None  # Memory (e.g., "512m", "1g")
    cpu_reservation: Optional[float] = None
    memory_reservation: Optional[str] = None

class ContainerUpdate(BaseModel):
    resource_limits: Optional[ResourceLimits] = None
    auto_restart: Optional[bool] = None
    restart_policy: Optional[str] = None

class DockerComposeStack(BaseModel):
    name: str
    compose_content: str
    description: Optional[str] = None

class NotificationConfig(BaseModel):
    email_enabled: bool = False
    email_from: Optional[str] = None
    email_to: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    webhook_url: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None

class BackupConfig(BaseModel):
    enabled: bool = False
    schedule: str = "0 2 * * *"  # Daily at 2 AM
    retention_days: int = 7
    backup_path: str = "/backup"
    include_containers: List[str] = []
    include_volumes: List[str] = []

# ============ LOGS WEBSOCKET ============

@advanced_router.websocket("/ws/logs/{container_id}")
async def container_logs_ws(websocket: WebSocket, container_id: str):
    await manager.connect(websocket, f"logs_{container_id}")
    
    try:
        docker_client = docker.from_env()
        container = docker_client.containers.get(container_id)
        
        # Send initial logs
        for line in container.logs(tail=100, stream=False).decode('utf-8').split('\n'):
            if line.strip():
                await websocket.send_text(line)
        
        # Stream new logs
        for line in container.logs(stream=True, follow=True):
            try:
                await websocket.send_text(line.decode('utf-8').strip())
            except WebSocketDisconnect:
                break
            
    except Exception as e:
        await websocket.send_text(f"Error: {str(e)}")
    finally:
        manager.disconnect(websocket, f"logs_{container_id}")

# ============ RESOURCE LIMITS ============

@advanced_router.get("/containers/{container_id}/resources")
async def get_container_resources(container_id: str):
    try:
        docker_client = docker.from_env()
        container = docker_client.containers.get(container_id)
        stats = container.stats(stream=False)
        
        return {
            "cpu_usage": stats['cpu_stats'],
            "memory_usage": stats['memory_stats'],
            "network": stats.get('networks', {}),
            "block_io": stats.get('blkio_stats', {})
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.put("/containers/{container_id}/resources")
async def update_container_resources(container_id: str, limits: ResourceLimits):
    try:
        docker_client = docker.from_env()
        container = docker_client.containers.get(container_id)
        
        update_config = {}
        if limits.cpu_limit:
            update_config['cpu_quota'] = int(limits.cpu_limit * 100000)
            update_config['cpu_period'] = 100000
        if limits.memory_limit:
            update_config['mem_limit'] = limits.memory_limit
        if limits.cpu_reservation:
            update_config['cpu_shares'] = int(limits.cpu_reservation * 1024)
        if limits.memory_reservation:
            update_config['mem_reservation'] = limits.memory_reservation
            
        container.update(**update_config)
        
        await notification_manager.send_notification(
            title=f"Resource Limits Updated",
            message=f"Container {container.name} resource limits updated",
            notification_type=NotificationType.INFO,
            channels=[],
            config=None
        )
        
        return {"success": True, "message": "Resource limits updated"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ IMAGE UPDATES ============

@advanced_router.get("/images/updates")
async def check_image_updates():
    try:
        docker_client = docker.from_env()
        containers = docker_client.containers.list(all=True)
        updates = []
        
        for container in containers:
            image = container.image
            image_name = image.tags[0] if image.tags else None
            
            if image_name:
                # Pull latest image
                try:
                    docker_client.images.pull(image_name)
                    latest_image = docker_client.images.get(image_name)
                    
                    if latest_image.id != image.id:
                        updates.append({
                            "container_id": container.id[:12],
                            "container_name": container.name,
                            "image": image_name,
                            "current_id": image.id[:12],
                            "latest_id": latest_image.id[:12],
                            "update_available": True
                        })
                except:
                    pass
        
        return {"updates": updates, "total": len(updates)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.post("/containers/{container_id}/update")
async def update_container_image(container_id: str):
    try:
        docker_client = docker.from_env()
        container = docker_client.containers.get(container_id)
        
        # Get container config
        image_name = container.image.tags[0] if container.image.tags else None
        if not image_name:
            raise HTTPException(status_code=400, detail="Cannot determine image name")
        
        # Pull latest image
        docker_client.images.pull(image_name)
        
        # Stop and remove old container
        container_config = container.attrs
        container.stop()
        container.remove()
        
        # Create new container with same config
        new_container = docker_client.containers.run(
            image_name,
            name=container_config['Name'].lstrip('/'),
            detach=True,
            environment=container_config['Config'].get('Env', []),
            ports=container_config['HostConfig'].get('PortBindings', {}),
            volumes=container_config['HostConfig'].get('Binds', [])
        )
        
        await notification_manager.send_notification(
            title=f"Container Updated",
            message=f"Container {container.name} updated to latest image",
            notification_type=NotificationType.SUCCESS,
            channels=[],
            config=None
        )
        
        return {"success": True, "new_container_id": new_container.id[:12]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ DOCKER COMPOSE ============

@advanced_router.post("/compose/deploy")
async def deploy_compose_stack(stack: DockerComposeStack):
    try:
        # Parse compose file
        compose_dict = yaml.safe_load(stack.compose_content)
        
        # Save compose file
        compose_dir = f"/tmp/compose_{stack.name}"
        os.makedirs(compose_dir, exist_ok=True)
        
        compose_file = os.path.join(compose_dir, "docker-compose.yml")
        with open(compose_file, 'w') as f:
            f.write(stack.compose_content)
        
        # Deploy using docker-compose
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "up", "-d"],
            capture_output=True,
            text=True,
            cwd=compose_dir
        )
        
        if result.returncode != 0:
            raise Exception(result.stderr)
        
        await notification_manager.send_notification(
            title=f"Stack Deployed",
            message=f"Docker Compose stack '{stack.name}' deployed successfully",
            notification_type=NotificationType.SUCCESS,
            channels=[],
            config=None
        )
        
        return {"success": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.get("/compose/stacks")
async def list_compose_stacks():
    # List all compose stacks
    stacks = []
    compose_base = "/tmp"
    
    for item in os.listdir(compose_base):
        if item.startswith("compose_"):
            stack_name = item.replace("compose_", "")
            compose_file = os.path.join(compose_base, item, "docker-compose.yml")
            if os.path.exists(compose_file):
                with open(compose_file, 'r') as f:
                    content = f.read()
                    stacks.append({
                        "name": stack_name,
                        "path": compose_file,
                        "services": len(yaml.safe_load(content).get('services', {}))
                    })
    
    return {"stacks": stacks}

@advanced_router.delete("/compose/{stack_name}")
async def remove_compose_stack(stack_name: str):
    try:
        compose_dir = f"/tmp/compose_{stack_name}"
        compose_file = os.path.join(compose_dir, "docker-compose.yml")
        
        if not os.path.exists(compose_file):
            raise HTTPException(status_code=404, detail="Stack not found")
        
        import subprocess
        result = subprocess.run(
            ["docker-compose", "-f", compose_file, "down", "-v"],
            capture_output=True,
            text=True,
            cwd=compose_dir
        )
        
        # Clean up files
        import shutil
        shutil.rmtree(compose_dir, ignore_errors=True)
        
        return {"success": True, "message": f"Stack {stack_name} removed"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ NOTIFICATIONS ============

@advanced_router.get("/notifications")
async def get_notifications(limit: int = 50):
    return {"notifications": notification_manager.get_notifications(limit)}

@advanced_router.post("/notifications/mark-read/{notification_id}")
async def mark_notification_read(notification_id: str):
    notification_manager.mark_as_read(notification_id)
    return {"success": True}

@advanced_router.post("/notifications/mark-all-read")
async def mark_all_notifications_read():
    notification_manager.mark_all_as_read()
    return {"success": True}

@advanced_router.post("/notifications/test")
async def test_notification(config: NotificationConfig):
    await notification_manager.send_notification(
        title="Test Notification",
        message="This is a test notification from Media Basher",
        notification_type=NotificationType.INFO,
        channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK, NotificationChannel.DISCORD, NotificationChannel.SLACK],
        config=config.model_dump()
    )
    return {"success": True, "message": "Test notification sent"}

# ============ NETWORK MANAGEMENT ============

@advanced_router.get("/networks")
async def list_networks():
    try:
        docker_client = docker.from_env()
        networks = docker_client.networks.list()
        
        return {
            "networks": [{
                "id": net.id[:12],
                "name": net.name,
                "driver": net.attrs['Driver'],
                "scope": net.attrs['Scope'],
                "containers": len(net.attrs.get('Containers', {}))
            } for net in networks]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.post("/networks")
async def create_network(name: str, driver: str = "bridge"):
    try:
        docker_client = docker.from_env()
        network = docker_client.networks.create(name, driver=driver)
        return {"success": True, "network_id": network.id[:12]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.delete("/networks/{network_id}")
async def remove_network(network_id: str):
    try:
        docker_client = docker.from_env()
        network = docker_client.networks.get(network_id)
        network.remove()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ HEALTH CHECK ============

@advanced_router.get("/health/system")
async def system_health_check():
    try:
        docker_client = docker.from_env()
        containers = docker_client.containers.list(all=True)
        
        health_score = 100
        issues = []
        
        # Check container health
        unhealthy = [c for c in containers if c.status != 'running']
        if unhealthy:
            health_score -= len(unhealthy) * 10
            issues.append(f"{len(unhealthy)} containers not running")
        
        # Check disk space
        import psutil
        disk = psutil.disk_usage('/')
        if disk.percent > 90:
            health_score -= 20
            issues.append("Disk usage above 90%")
        elif disk.percent > 80:
            health_score -= 10
            issues.append("Disk usage above 80%")
        
        # Check memory
        ram = psutil.virtual_memory()
        if ram.percent > 90:
            health_score -= 15
            issues.append("Memory usage above 90%")
        elif ram.percent > 80:
            health_score -= 5
            issues.append("Memory usage above 80%")
        
        health_score = max(0, health_score)
        
        status = "excellent" if health_score >= 90 else "good" if health_score >= 70 else "fair" if health_score >= 50 else "poor"
        
        return {
            "health_score": health_score,
            "status": status,
            "issues": issues,
            "total_containers": len(containers),
            "running_containers": len([c for c in containers if c.status == 'running'])
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ METRICS HISTORY ============

@advanced_router.get("/metrics/history")
async def get_metrics_history(hours: int = 1):
    """Get historical metrics for the last N hours"""
    metrics = metrics_collector.get_metrics(hours)
    return {"metrics": metrics, "count": len(metrics)}

@advanced_router.get("/metrics/aggregated")
async def get_aggregated_metrics(hours: int = 24):
    """Get aggregated statistics"""
    stats = metrics_collector.get_aggregated_metrics(hours)
    return stats

@advanced_router.post("/metrics/start-collection")
async def start_metrics_collection(background_tasks: BackgroundTasks):
    """Start background metrics collection"""
    background_tasks.add_task(metrics_collector.start_collection)
    return {"success": True, "message": "Metrics collection started"}

@advanced_router.post("/metrics/stop-collection")
async def stop_metrics_collection():
    """Stop background metrics collection"""
    metrics_collector.stop_collection()
    return {"success": True, "message": "Metrics collection stopped"}

# ============ BACKUP SYSTEM ============

class BackupConfigModel(BaseModel):
    backup_path: str = "/backup"
    backup_mongodb: bool = True
    include_volumes: Optional[List[str]] = []
    include_containers: Optional[List[str]] = []

@advanced_router.post("/backup/create")
async def create_backup(config: BackupConfigModel, background_tasks: BackgroundTasks):
    """Create a system backup"""
    backup_info = await backup_manager.create_backup(config.model_dump())
    
    if backup_info['status'] == 'completed':
        await notification_manager.send_notification(
            title="Backup Completed",
            message=f"Backup {backup_info['id']} created successfully",
            notification_type=NotificationType.SUCCESS,
            channels=[],
            config=None
        )
    
    return backup_info

@advanced_router.get("/backup/list")
async def list_backups(backup_path: str = "/backup"):
    """List all available backups"""
    backups = backup_manager.list_backups(backup_path)
    return {"backups": backups}

@advanced_router.post("/backup/restore")
async def restore_backup(backup_path: str):
    """Restore from a backup file"""
    success = await backup_manager.restore_backup(backup_path)
    
    if success:
        await notification_manager.send_notification(
            title="Backup Restored",
            message="System restored from backup successfully",
            notification_type=NotificationType.SUCCESS,
            channels=[],
            config=None
        )
        return {"success": True, "message": "Backup restored"}
    else:
        raise HTTPException(status_code=400, detail="Restore failed")

# ============ RESOURCE MANAGEMENT UI ============

class ResourceLimitsUI(BaseModel):
    container_id: str
    cpu_limit: Optional[float] = None
    memory_limit: Optional[str] = None
    restart_policy: Optional[str] = "unless-stopped"

@advanced_router.post("/containers/set-limits")
async def set_container_limits(limits: ResourceLimitsUI):
    """Set resource limits for a container"""
    try:
        docker_client = docker.from_env()
        container = docker_client.containers.get(limits.container_id)
        
        update_config = {"restart_policy": {"Name": limits.restart_policy}}
        
        if limits.cpu_limit:
            update_config['cpu_quota'] = int(limits.cpu_limit * 100000)
            update_config['cpu_period'] = 100000
        
        if limits.memory_limit:
            update_config['mem_limit'] = limits.memory_limit
        
        container.update(**update_config)
        
        await notification_manager.send_notification(
            title="Resource Limits Updated",
            message=f"Container {container.name} limits configured",
            notification_type=NotificationType.INFO,
            channels=[],
            config=None
        )
        
        return {"success": True, "message": "Limits applied"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.get("/containers/{container_id}/limits")
async def get_container_limits(container_id: str):
    """Get current resource limits for a container"""
    try:
        docker_client = docker.from_env()
        container = docker_client.containers.get(container_id)
        
        host_config = container.attrs.get('HostConfig', {})
        
        cpu_quota = host_config.get('CpuQuota', 0)
        cpu_period = host_config.get('CpuPeriod', 100000)
        cpu_limit = cpu_quota / cpu_period if cpu_quota > 0 else None
        
        memory_limit = host_config.get('Memory', 0)
        
        return {
            "cpu_limit": cpu_limit,
            "memory_limit": memory_limit,
            "memory_limit_str": f"{memory_limit // (1024*1024)}m" if memory_limit > 0 else None,
            "restart_policy": host_config.get('RestartPolicy', {}).get('Name', 'no')
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# ============ ALERT MANAGEMENT ============

from alert_manager import alert_manager, AlertRule
import uuid

class AlertRuleModel(BaseModel):
    name: str
    metric: str  # cpu, ram, disk
    threshold: float
    comparison: str  # gt, lt
    enabled: bool = True

@advanced_router.get("/alerts/rules")
async def get_alert_rules():
    """Get all alert rules"""
    return {"rules": alert_manager.get_rules()}

@advanced_router.post("/alerts/rules")
async def create_alert_rule(rule: AlertRuleModel):
    """Create a new alert rule"""
    rule_id = str(uuid.uuid4())
    alert_rule = AlertRule(
        rule_id=rule_id,
        name=rule.name,
        metric=rule.metric,
        threshold=rule.threshold,
        comparison=rule.comparison,
        enabled=rule.enabled
    )
    alert_manager.add_rule(alert_rule)
    return {"success": True, "rule_id": rule_id}

@advanced_router.delete("/alerts/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """Delete an alert rule"""
    alert_manager.remove_rule(rule_id)
    return {"success": True}

@advanced_router.put("/alerts/rules/{rule_id}")
async def update_alert_rule(rule_id: str, updates: Dict):
    """Update an alert rule"""
    alert_manager.update_rule(rule_id, updates)
    return {"success": True}

@advanced_router.post("/alerts/start-monitoring")
async def start_alert_monitoring(background_tasks: BackgroundTasks, config: Optional[NotificationConfig] = None):
    """Start alert monitoring"""
    if config:
        alert_manager.set_notification_config(config.model_dump())
    background_tasks.add_task(alert_manager.start_monitoring)
    return {"success": True, "message": "Alert monitoring started"}

@advanced_router.post("/alerts/stop-monitoring")
async def stop_alert_monitoring():
    """Stop alert monitoring"""
    alert_manager.stop_monitoring()
    return {"success": True, "message": "Alert monitoring stopped"}

# ============ SCHEDULED BACKUPS ============

from backup_scheduler import backup_scheduler

class BackupScheduleModel(BaseModel):
    name: str
    cron_expression: str
    backup_config: BackupConfigModel

@advanced_router.get("/backup/schedules")
async def get_backup_schedules():
    """Get all backup schedules"""
    schedules = backup_scheduler.get_schedules()
    return {"schedules": schedules}

@advanced_router.post("/backup/schedules")
async def create_backup_schedule(schedule: BackupScheduleModel):
    """Create a new backup schedule"""
    schedule_id = str(uuid.uuid4())
    backup_scheduler.add_schedule(schedule_id, schedule.cron_expression, schedule.backup_config.model_dump())
    return {"success": True, "schedule_id": schedule_id}

@advanced_router.delete("/backup/schedules/{schedule_id}")
async def delete_backup_schedule(schedule_id: str):
    """Delete a backup schedule"""
    backup_scheduler.remove_schedule(schedule_id)
    return {"success": True}

@advanced_router.post("/backup/schedules/{schedule_id}/pause")
async def pause_backup_schedule(schedule_id: str):
    """Pause a backup schedule"""
    backup_scheduler.pause_schedule(schedule_id)
    return {"success": True}

@advanced_router.post("/backup/schedules/{schedule_id}/resume")
async def resume_backup_schedule(schedule_id: str):
    """Resume a backup schedule"""
    backup_scheduler.resume_schedule(schedule_id)
    return {"success": True}

# ============ CONTAINER RESOURCE HEATMAP ============

@advanced_router.get("/containers/resource-heatmap")
async def get_container_resource_heatmap():
    """Get resource usage for all containers"""
    try:
        docker_client = docker.from_env()
        containers = docker_client.containers.list()
        
        heatmap_data = []
        for container in containers:
            try:
                stats = container.stats(stream=False)
                
                # Calculate CPU percentage
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
                cpu_percent = (cpu_delta / system_delta) * len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0 if system_delta > 0 else 0
                
                # Calculate memory percentage
                mem_usage = stats['memory_stats']['usage']
                mem_limit = stats['memory_stats']['limit']
                mem_percent = (mem_usage / mem_limit) * 100 if mem_limit > 0 else 0
                
                heatmap_data.append({
                    "id": container.id[:12],
                    "name": container.name,
                    "cpu_percent": round(cpu_percent, 2),
                    "memory_percent": round(mem_percent, 2),
                    "memory_usage": mem_usage,
                    "memory_limit": mem_limit,
                    "status": container.status
                })
            except Exception as e:
                logger.error(f"Error getting stats for container {container.name}: {e}")
        
        return {"containers": heatmap_data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ MULTI-CONTAINER LOG AGGREGATION ============

@advanced_router.get("/logs/aggregate")
async def aggregate_logs(container_ids: str, lines: int = 100):
    """Aggregate logs from multiple containers"""
    try:
        docker_client = docker.from_env()
        ids = container_ids.split(',')
        
        aggregated_logs = []
        for container_id in ids:
            try:
                container = docker_client.containers.get(container_id.strip())
                logs = container.logs(tail=lines, timestamps=True).decode('utf-8')
                
                for line in logs.split('\n'):
                    if line.strip():
                        aggregated_logs.append({
                            "container_id": container_id[:12],
                            "container_name": container.name,
                            "log": line
                        })
            except Exception as e:
                logger.error(f"Error getting logs for {container_id}: {e}")
        
        # Sort by timestamp if available
        aggregated_logs.sort(key=lambda x: x['log'])
        
        return {"logs": aggregated_logs[-lines:]}  # Return last N lines
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============ VPN CONFIGURATION ============

class VPNConfig(BaseModel):
    vpn_type: str  # wireguard or openvpn
    server_address: str
    server_port: int
    private_key: Optional[str] = None
    public_key: Optional[str] = None
    config_file: Optional[str] = None

@advanced_router.post("/vpn/configure")
async def configure_vpn(config: VPNConfig):
    """Configure VPN (WireGuard or OpenVPN)"""
    try:
        # This is a placeholder for VPN configuration
        # In production, this would set up WireGuard/OpenVPN configs
        
        if config.vpn_type == "wireguard":
            # Generate WireGuard config
            wg_config = f\"\"\"[Interface]
PrivateKey = {config.private_key or 'GENERATE_NEW_KEY'}
Address = 10.0.0.2/24

[Peer]
PublicKey = {config.public_key or 'SERVER_PUBLIC_KEY'}
Endpoint = {config.server_address}:{config.server_port}
AllowedIPs = 0.0.0.0/0
\"\"\"
            # Save config (in production, save to /etc/wireguard/)
            return {"success": True, "config": wg_config, "message": "WireGuard configured"}
        
        elif config.vpn_type == "openvpn":
            # OpenVPN configuration
            return {"success": True, "message": "OpenVPN configuration requires .ovpn file upload"}
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported VPN type")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@advanced_router.get("/vpn/status")
async def get_vpn_status():
    """Get VPN connection status"""
    try:
        # Check if WireGuard is running
        import subprocess
        result = subprocess.run(["wg", "show"], capture_output=True, text=True)
        
        if result.returncode == 0 and result.stdout:
            return {"connected": True, "type": "wireguard", "status": result.stdout}
        else:
            return {"connected": False, "message": "No active VPN connection"}
    except Exception as e:
        return {"connected": False, "message": str(e)}

