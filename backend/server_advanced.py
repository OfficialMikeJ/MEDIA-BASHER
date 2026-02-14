# Advanced features extension for Media Basher
# This file contains additional routes for advanced features

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, UploadFile, File
from typing import Dict, List, Optional
from pydantic import BaseModel
import docker
import asyncio
import yaml
import os
from websocket_manager import manager
from notifications import notification_manager, NotificationType, NotificationChannel

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
