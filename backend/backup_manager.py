# Backup management system for Media Basher
import os
import subprocess
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
import shutil

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        self.backup_jobs: List[Dict] = []
        self.is_running = False

    async def create_backup(self, backup_config: Dict) -> Dict:
        """Create a backup based on configuration"""
        backup_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_config['backup_path'], f"backup_{backup_id}")
        
        try:
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup MongoDB
            if backup_config.get('backup_mongodb', True):
                mongo_backup_path = os.path.join(backup_path, 'mongodb')
                await self._backup_mongodb(mongo_backup_path)
            
            # Backup Docker volumes
            if backup_config.get('include_volumes'):
                volumes_backup_path = os.path.join(backup_path, 'volumes')
                await self._backup_volumes(backup_config['include_volumes'], volumes_backup_path)
            
            # Backup container configs
            if backup_config.get('include_containers'):
                configs_backup_path = os.path.join(backup_path, 'configs')
                await self._backup_container_configs(backup_config['include_containers'], configs_backup_path)
            
            # Compress backup
            archive_path = f"{backup_path}.tar.gz"
            await self._compress_backup(backup_path, archive_path)
            
            # Remove uncompressed backup
            shutil.rmtree(backup_path)
            
            backup_info = {
                "id": backup_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "path": archive_path,
                "size": os.path.getsize(archive_path),
                "status": "completed"
            }
            
            self.backup_jobs.append(backup_info)
            logger.info(f"Backup created: {backup_id}")
            
            return backup_info
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return {
                "id": backup_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "failed",
                "error": str(e)
            }

    async def _backup_mongodb(self, output_path: str):
        """Backup MongoDB database"""
        os.makedirs(output_path, exist_ok=True)
        
        try:
            result = subprocess.run(
                ["mongodump", "--out", output_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"MongoDB backup failed: {result.stderr}")
                raise Exception(result.stderr)
                
            logger.info(f"MongoDB backed up to {output_path}")
        except Exception as e:
            logger.warning(f"MongoDB backup not available: {e}")

    async def _backup_volumes(self, volume_names: List[str], output_path: str):
        """Backup Docker volumes"""
        os.makedirs(output_path, exist_ok=True)
        
        for volume in volume_names:
            try:
                volume_backup = os.path.join(output_path, f"{volume}.tar")
                result = subprocess.run(
                    [
                        "docker", "run", "--rm",
                        "-v", f"{volume}:/volume",
                        "-v", f"{output_path}:/backup",
                        "busybox",
                        "tar", "czf", f"/backup/{volume}.tar", "-C", "/volume", "."
                    ],
                    capture_output=True,
                    text=True,
                    timeout=600
                )
                
                if result.returncode == 0:
                    logger.info(f"Volume {volume} backed up")
                else:
                    logger.error(f"Volume backup failed for {volume}: {result.stderr}")
                    
            except Exception as e:
                logger.error(f"Error backing up volume {volume}: {e}")

    async def _backup_container_configs(self, container_ids: List[str], output_path: str):
        """Backup container configurations"""
        os.makedirs(output_path, exist_ok=True)
        
        try:
            import docker
            docker_client = docker.from_env()
            
            for container_id in container_ids:
                try:
                    container = docker_client.containers.get(container_id)
                    config = container.attrs
                    
                    config_file = os.path.join(output_path, f"{container.name}.json")
                    import json
                    with open(config_file, 'w') as f:
                        json.dump(config, f, indent=2)
                    
                    logger.info(f"Container config backed up: {container.name}")
                except Exception as e:
                    logger.error(f"Error backing up container {container_id}: {e}")
                    
        except Exception as e:
            logger.error(f"Docker not available for container backup: {e}")

    async def _compress_backup(self, source_path: str, archive_path: str):
        """Compress backup directory"""
        try:
            result = subprocess.run(
                ["tar", "czf", archive_path, "-C", os.path.dirname(source_path), os.path.basename(source_path)],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                raise Exception(result.stderr)
                
            logger.info(f"Backup compressed to {archive_path}")
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            raise

    def list_backups(self, backup_path: str) -> List[Dict]:
        """List all available backups"""
        if not os.path.exists(backup_path):
            return []
        
        backups = []
        for filename in os.listdir(backup_path):
            if filename.startswith("backup_") and filename.endswith(".tar.gz"):
                filepath = os.path.join(backup_path, filename)
                backups.append({
                    "filename": filename,
                    "path": filepath,
                    "size": os.path.getsize(filepath),
                    "created": datetime.fromtimestamp(os.path.getctime(filepath)).isoformat()
                })
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

    async def restore_backup(self, backup_path: str) -> bool:
        """Restore from a backup file"""
        try:
            # Extract backup
            extract_path = backup_path.replace(".tar.gz", "")
            result = subprocess.run(
                ["tar", "xzf", backup_path, "-C", os.path.dirname(backup_path)],
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                raise Exception(result.stderr)
            
            # Restore MongoDB
            mongo_path = os.path.join(extract_path, 'mongodb')
            if os.path.exists(mongo_path):
                await self._restore_mongodb(mongo_path)
            
            logger.info(f"Backup restored from {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

    async def _restore_mongodb(self, backup_path: str):
        """Restore MongoDB from backup"""
        try:
            result = subprocess.run(
                ["mongorestore", backup_path],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                raise Exception(result.stderr)
                
            logger.info("MongoDB restored")
        except Exception as e:
            logger.error(f"MongoDB restore failed: {e}")
            raise

backup_manager = BackupManager()