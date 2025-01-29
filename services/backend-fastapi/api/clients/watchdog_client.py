from typing import Optional, Dict, Any, List, Union
import aiohttp
import asyncio
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException
import json
import uuid

class WatchdogClient:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        service_name: str,
        instance_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.service_name = service_name
        self.instance_id = instance_id or str(uuid.uuid4())
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = logging.getLogger("watchdog_client")
        
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Service-Name": service_name,
            "X-Instance-ID": self.instance_id
        }
        
        # Heartbeat task
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._heartbeat_interval = 30  # seconds
        self._is_running = False

    async def _register_instance(self) -> None:
        """
        Register this instance with the watchdog service
        """
        endpoint = f"{self.base_url}/v1/register"
        
        registration_data = {
            "service_name": self.service_name,
            "instance_id": self.instance_id,
            "start_time": datetime.utcnow().isoformat(),
            "metadata": {
                "version": "1.0.0",
                "environment": "production"
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=registration_data,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 201:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Registration failed')
                        )
        except Exception as e:
            self.logger.error(f"Failed to register instance: {str(e)}")
            raise

    async def _deregister_instance(self) -> None:
        """
        Deregister this instance from the watchdog service
        """
        endpoint = f"{self.base_url}/v1/deregister"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Deregistration failed')
                        )
        except Exception as e:
            self.logger.error(f"Failed to deregister instance: {str(e)}")
            raise

    async def _heartbeat_loop(self) -> None:
        """
        Main heartbeat loop
        """
        while self._is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self._heartbeat_interval)
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {str(e)}")
                await asyncio.sleep(5)  # Wait before retry

    async def _send_heartbeat(self) -> None:
        """
        Send a single heartbeat to the watchdog service
        """
        endpoint = f"{self.base_url}/v1/heartbeat"
        
        heartbeat_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "healthy",
            "metadata": {
                "cpu_usage": 0.5,  # Example metrics
                "memory_usage": 0.3
            }
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=heartbeat_data,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Heartbeat failed')
                        )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Heartbeat failed: {str(e)}"
            )

    async def start(self) -> None:
        """
        Start the watchdog client and begin sending heartbeats
        """
        if self._is_running:
            return

        try:
            # Register instance
            await self._register_instance()
            
            # Start heartbeat
            self._is_running = True
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            self.logger.info(f"Watchdog client started for service {self.service_name}")
        except Exception as e:
            self.logger.error(f"Failed to start watchdog client: {str(e)}")
            raise

    async def stop(self) -> None:
        """
        Stop the watchdog client and cleanup
        """
        if not self._is_running:
            return

        try:
            self._is_running = False
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Deregister instance
            await self._deregister_instance()
            
            self.logger.info(f"Watchdog client stopped for service {self.service_name}")
        except Exception as e:
            self.logger.error(f"Error stopping watchdog client: {str(e)}")
            raise

    async def report_status(
        self,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Report service status to watchdog
        """
        endpoint = f"{self.base_url}/v1/status"
        
        status_data = {
            "status": status,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=status_data,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to report status')
                        )
        except Exception as e:
            self.logger.error(f"Failed to report status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Watchdog service error: {str(e)}"
            )

    async def report_health(
        self,
        checks: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Report detailed health status to watchdog
        """
        endpoint = f"{self.base_url}/v1/health"
        
        health_data = {
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=health_data,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to report health status')
                        )
        except Exception as e:
            self.logger.error(f"Failed to report health status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Watchdog service error: {str(e)}"
            )

    async def report_dependency_status(
        self,
        dependency_name: str,
        status: str,
        latency: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Report dependency status to watchdog
        """
        endpoint = f"{self.base_url}/v1/dependencies"
        
        dependency_data = {
            "name": dependency_name,
            "status": status,
            "latency": latency,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=dependency_data,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to report dependency status')
                        )
        except Exception as e:
            self.logger.error(f"Failed to report dependency status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Watchdog service error: {str(e)}"
            )

    async def set_maintenance_mode(
        self,
        enabled: bool,
        reason: Optional[str] = None,
        duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Set or unset maintenance mode for the service
        """
        endpoint = f"{self.base_url}/v1/maintenance"
        
        maintenance_data = {
            "enabled": enabled,
            "reason": reason,
            "duration": duration,  # Duration in seconds
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    endpoint,
                    json=maintenance_data,
                    headers=self.headers,
                    timeout=self.timeout
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_data = await response.json()
                        raise HTTPException(
                            status_code=response.status,
                            detail=error_data.get('detail', 'Failed to set maintenance mode')
                        )
        except Exception as e:
            self.logger.error(f"Failed to set maintenance mode: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Watchdog service error: {str(e)}"
            )