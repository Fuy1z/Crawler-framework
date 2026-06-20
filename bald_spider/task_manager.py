import asyncio
from typing import Set,Final
from asyncio import Task,Future,Semaphore



class TaskManager:

    def __init__(self,total_concurrency: int=8):
        self.current_task: Final[Set[Task]] = set()
        self.semaphore: Semaphore = Semaphore(total_concurrency)

    def create_task(self, coroutine):
        task = asyncio.create_task(coroutine)
        self.current_task.add(task)

        def done_callback(_fut: Task[Future]):
            self.current_task.remove(task)
            self.semaphore.release()

        task.add_done_callback(done_callback)
        return task

    def all_done(self) -> bool:
        return len(self.current_task) == 0