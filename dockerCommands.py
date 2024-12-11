import asyncio
import json
from typing import Dict, List, Optional, Tuple
from loguru import logger
from pydantic import BaseModel, field_validator

class ContainerInfo(BaseModel):
    Command: str
    CreatedAt: str
    ID: str
    Image: str
    Labels: Dict[str, str] = {}
    LocalVolumes: int
    Mounts: Optional[List[str]] = []
    Names: str
    Networks: Optional[List[str]] = []
    Ports: Optional[List[str]] = []
    RunningFor: str
    Size: str
    State: str
    Status: str
    Compose: bool = False

    @field_validator('Labels', mode='before')
    def parse_labels(cls, v):
        if not v:
            return {}
        labels = {}
        last_key = ""
        for item in v.split(','):
            if '=' in item:
                last_key = item.split('=')[0]
                labels[item.split('=')[0]] = item.split('=')[1]
            else:
                labels[last_key] += (',' + item)
        return labels

    @field_validator('Mounts', 'Networks', 'Ports', mode='before')
    def parse_comma_separated(cls, v):
        if not v:
            return []
        return v.split(',')
    
    def __init__(self, **data):
        super().__init__(**data)
        self.set_compose()
    
    def set_compose(self):
        self.Compose = bool(self.Labels) and "com.docker.compose.config-hash" in self.Labels


class DokerCommandRunner():

    @staticmethod
    async def execute_command(cmd: str, cwd: str | None = None) -> Tuple[int, str, str]:
        logger.info(f"Executed: \"{cmd}\"{ ' in: ' + cwd if cwd else ''}")
        result = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd= cwd
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
    async def docker_compose_up(container_id: str) -> str:
        container = [cont for cont in await DokerCommandRunner.list_containers() if cont.ID == container_id]
        if container and container[0].Compose:
            cmd = f"docker-compose up -d"
            _, _, _ = await DokerCommandRunner.execute_command(cmd, cwd = container[0].Labels.get("com.docker.compose.project.working_dir", None))
            return "complete"
        else:
            return "Container not in docker compose"
    

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