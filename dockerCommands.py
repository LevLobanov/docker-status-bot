import asyncio
import json
from sys import stdin
from typing import Dict, List, Optional, Tuple
from loguru import logger
from pydantic import BaseModel, field_validator

class ContainerInfo(BaseModel):
    Command: str
    CreatedAt: str
    ID: str
    Image: str
    Labels: Optional[List[Dict[str, str]]] = []
    LocalVolumes: int
    Mounts: Optional[List[str]] = []
    Names: str
    Networks: Optional[List[str]] = []
    Ports: Optional[List[str]] = []
    RunningFor: str
    Size: str
    State: str
    Status: str

    @field_validator('Labels', mode='before')
    def parse_labels(cls, v):
        if not v:
            return []
        return [{item.split('=')[0]: item.split('=')[1]} for item in v.split(',')]

    @field_validator('Mounts', 'Networks', 'Ports', mode='before')
    def parse_comma_separated(cls, v):
        if not v:
            return []
        return v.split(',')


class DokerCommandRunner():

    @staticmethod
    async def execute_command(cmd: str) -> Tuple[int, str, str]:
        logger.info("Executed: \"{cmd}\"")
        result = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await result.communicate()
        return (
            result.returncode if result.returncode else -1,
            stdout.decode(),
            stderr.decode()
        )


    @staticmethod
    async def list_containers() -> List[ContainerInfo]:
        cmd = "docker ps -a -n 10 --format '{{json .}}'"
        _, stdout, stderr = await DokerCommandRunner.execute_command(cmd)
        if not stderr:
            containers = [ContainerInfo(**json.loads(json_container)) for json_container in stdout.split("\n") if json_container]
            return containers
        return []
    
    
    @staticmethod
    async def show_container_logs(container_id: str) -> Optional[str]:
        cmd = f"docker logs {container_id} -t -n 25"
        _, _, stderr = await DokerCommandRunner.execute_command(cmd)
        if stderr:
            return stderr
        
    
    @staticmethod
    async def up_container(container_id: str) -> bool:
        cmd = f"docker start {container_id}"
        _, _, stderr = await DokerCommandRunner.execute_command(cmd)
        if not stderr:
            return True
        return False
    

    @staticmethod
    async def stop_container(container_id: str) -> bool:
        cmd = f"docker stop {container_id}"
        _, _, stderr = await DokerCommandRunner.execute_command(cmd)
        if not stderr:
            return True
        return False
    

    @staticmethod
    async def pause_container(container_id: str) -> bool:
        cmd = f"docker pause {container_id}"
        _, _, stderr = await DokerCommandRunner.execute_command(cmd)
        if not stderr:
            return True
        return False
    

    @staticmethod
    async def unpause_container(container_id: str) -> bool:
        cmd = f"docker unpause {container_id}"
        _, _, stderr = await DokerCommandRunner.execute_command(cmd)
        if not stderr:
            return True
        return False


if __name__ == "__main__":
    print(asyncio.run(DokerCommandRunner.list_containers()))