import asyncio
import json
from typing import Dict, List, Optional, Tuple
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
        _, stdout, stderr = await DokerCommandRunner.execute_command(cmd)
        if not stderr:
            return stdout


if __name__ == "__main__":
    print(asyncio.run(DokerCommandRunner.list_containers()))