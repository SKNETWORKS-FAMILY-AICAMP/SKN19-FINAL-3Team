"""
사용법 참고:

RedisRepository는 Redis 연결과 큐 작업 같은 외부 스토리지 I/O만 담당한다.
비즈니스 로직은 Service에서 다룬다.
"""

import json
from typing import Optional

import redis.asyncio as redis

from common.core.codes import LlmTaskStatus
from common.core.config import settings


class RedisRepository:
    """Redis 큐에 메시지를 넣고 연결을 관리하는 저장소."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)

    async def enqueue(self, key_name: str, payload: dict):
        """
        지정한 큐에 작업을 추가하고, 동시에 payload 데이터를 기반으로 상태 메타데이터(Hash)를 생성합니다.
        
        :param key_name: payload에서 식별자로 사용할 필드명 (예: 'task_id')
        :param payload: 작업 데이터 (이 전체 내용이 Hash에도 저장됨)
        """
        queue_name = settings.QUEUE_NAME
        
        # 1. 식별자 값 추출
        id_value = payload.get(key_name)

        async with self.redis.pipeline(transaction=True) as pipe:
            # 2. 메타데이터(Hash) 저장 준비
            if id_value:
                # Redis Hash Key 생성 (예: key_name="task_id" -> "task_id:xxxx")
                redis_key = f"{key_name}:{id_value}"
                
                # Payload 전체를 메타데이터로 활용
                mapping = payload.copy()
                
                pipe.hset(redis_key, mapping=mapping)
                # 24시간 후 만료 (TTL 설정)
                pipe.expire(redis_key, 86400)

            # 3. 큐에 작업 추가 준비
            pipe.lpush(queue_name, json.dumps(payload))

            # 4. 일괄 실행 (Atomic)
            await pipe.execute()

    async def set_task_metadata(self, task_id: str, status: LlmTaskStatus, **kwargs):
        """작업 상태 및 추가 메타데이터 저장."""
        key = f"task_id:{task_id}"
        mapping = {"task_status": status.value}
        if kwargs:
            mapping.update(kwargs)
        await self.redis.hset(key, mapping=mapping)

    async def get_task_metadata(self, task_id: str) -> Optional[dict]:
        """작업 상태 해시를 조회. 없으면 None 반환."""
        key = f"task_id:{task_id}"
        data = await self.redis.hgetall(key)
        return data or None

    async def dequeue(self, timeout: int = 5) -> Optional[dict]:
        """큐에서 작업을 가져옴 (BPOP)."""
        queue_name = settings.QUEUE_NAME
        task = await self.redis.brpop(queue_name, timeout=timeout)
        if task:
            _, data = task
            return json.loads(data)
        return None

    async def close(self):
        """Redis 연결을 정리."""
        await self.redis.close()