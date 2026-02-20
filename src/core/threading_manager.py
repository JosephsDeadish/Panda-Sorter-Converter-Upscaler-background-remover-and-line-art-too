"""
Thread Pool Management for Game Texture Sorter.

This module provides a comprehensive threading system for managing concurrent
operations such as texture loading, processing, and thumbnail generation.

Author: Dead On The Inside / JosephsDeadish
"""

import logging
import queue
import threading
import time
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from uuid import uuid4


logger = logging.getLogger(__name__)


class TaskPriority(Enum):
    """Priority levels for task execution."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class TaskStatus(Enum):
    """Status of a task in the queue."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Represents a task to be executed by the thread pool."""
    task_id: str
    func: Callable
    args: tuple
    kwargs: dict
    callback: Optional[Callable[[Any], None]]
    error_callback: Optional[Callable[[Exception], None]]
    priority: TaskPriority
    status: TaskStatus
    future: Optional[Future] = None
    created_at: float = 0.0
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    result: Any = None
    error: Optional[Exception] = None

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    def __lt__(self, other):
        """Compare tasks by priority for priority queue."""
        return self.priority.value > other.priority.value


class ThreadingManager:
    """
    Manages worker thread pools with support for concurrent operations.
    
    Features:
    - Configurable thread count (1-16 threads)
    - Background thumbnail loading
    - Non-blocking operations with callbacks
    - Task queue management with priorities
    - Thread safety with proper locking
    - Pause/resume functionality
    - Graceful shutdown
    
    Example:
        >>> manager = ThreadingManager(thread_count=4)
        >>> manager.start()
        >>> task_id = manager.submit_task(
        ...     process_image,
        ...     args=("image.png",),
        ...     callback=on_complete,
        ...     priority=TaskPriority.HIGH
        ... )
        >>> manager.shutdown()
    """

    MIN_THREADS = 1
    MAX_THREADS = 16

    def __init__(
        self,
        thread_count: int = 4,
        max_queue_size: int = 1000,
        name: str = "ThreadingManager"
    ):
        """
        Initialize the ThreadingManager.
        
        Args:
            thread_count: Number of worker threads (1-16)
            max_queue_size: Maximum size of the task queue
            name: Name for this manager instance (used in logging)
            
        Raises:
            ValueError: If thread_count is not in valid range
        """
        if not self.MIN_THREADS <= thread_count <= self.MAX_THREADS:
            raise ValueError(
                f"thread_count must be between {self.MIN_THREADS} and "
                f"{self.MAX_THREADS}, got {thread_count}"
            )

        self.name = name
        self._thread_count = thread_count
        self._max_queue_size = max_queue_size
        
        # Thread pool and queue
        self._executor: Optional[ThreadPoolExecutor] = None
        self._task_queue: queue.PriorityQueue = queue.PriorityQueue(
            maxsize=max_queue_size
        )
        
        # Task tracking
        self._tasks: Dict[str, Task] = {}
        self._tasks_lock = threading.RLock()
        self._active_tasks: Set[str] = set()
        
        # State management
        self._running = False
        self._paused = False
        self._shutdown_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.set()  # Not paused initially
        
        # Worker thread for queue processing
        self._queue_worker: Optional[threading.Thread] = None
        
        # Statistics
        self._total_submitted = 0
        self._total_completed = 0
        self._total_failed = 0
        self._total_cancelled = 0
        
        logger.info(
            f"{self.name}: Initialized with {thread_count} threads, "
            f"max queue size: {max_queue_size}"
        )

    def start(self) -> None:
        """Start the threading manager and worker threads."""
        if self._running:
            logger.warning(f"{self.name}: Already running")
            return

        logger.info(f"{self.name}: Starting...")
        
        self._running = True
        self._shutdown_event.clear()
        
        # Create thread pool
        self._executor = ThreadPoolExecutor(
            max_workers=self._thread_count,
            thread_name_prefix=f"{self.name}_Worker"
        )
        
        # Start queue processing thread
        self._queue_worker = threading.Thread(
            target=self._process_queue,
            name=f"{self.name}_QueueWorker",
            daemon=True
        )
        self._queue_worker.start()
        
        logger.info(f"{self.name}: Started successfully")

    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """
        Shutdown the threading manager gracefully.
        
        Args:
            wait: If True, wait for all tasks to complete
            timeout: Maximum time to wait for shutdown (seconds)
        """
        if not self._running:
            logger.warning(f"{self.name}: Not running")
            return

        logger.info(f"{self.name}: Shutting down...")
        
        self._running = False
        self._shutdown_event.set()
        self._pause_event.set()  # Unpause if paused
        
        # Cancel pending tasks
        self._cancel_pending_tasks()
        
        # Wait for queue worker
        if self._queue_worker and self._queue_worker.is_alive():
            self._queue_worker.join(timeout=5.0)
        
        # Shutdown executor
        if self._executor:
            self._executor.shutdown(wait=wait, cancel_futures=not wait)
            self._executor = None
        
        logger.info(
            f"{self.name}: Shutdown complete. "
            f"Stats - Submitted: {self._total_submitted}, "
            f"Completed: {self._total_completed}, "
            f"Failed: {self._total_failed}, "
            f"Cancelled: {self._total_cancelled}"
        )

    def submit_task(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        callback: Optional[Callable[[Any], None]] = None,
        error_callback: Optional[Callable[[Exception], None]] = None,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Submit a task for execution.
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            callback: Called with result when task completes successfully
            error_callback: Called with exception if task fails
            priority: Task priority level
            
        Returns:
            Unique task ID for tracking
            
        Raises:
            RuntimeError: If manager is not running
            queue.Full: If task queue is full
        """
        if not self._running:
            raise RuntimeError(f"{self.name}: Manager is not running")

        task_id = str(uuid4())
        task = Task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs or {},
            callback=callback,
            error_callback=error_callback,
            priority=priority,
            status=TaskStatus.PENDING
        )
        
        with self._tasks_lock:
            self._tasks[task_id] = task
            self._total_submitted += 1
        
        try:
            self._task_queue.put(task, block=False)
            logger.debug(
                f"{self.name}: Task {task_id} queued with priority "
                f"{priority.name}"
            )
        except queue.Full:
            with self._tasks_lock:
                del self._tasks[task_id]
                self._total_submitted -= 1
            raise
        
        return task_id

    def submit_background_load(
        self,
        load_func: Callable,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        callback: Optional[Callable[[Any], None]] = None
    ) -> str:
        """
        Submit a background loading task (e.g., thumbnail loading).
        
        This is a convenience method for submitting low-priority tasks
        typically used for non-urgent background operations.
        
        Args:
            load_func: Function to load data
            args: Positional arguments
            kwargs: Keyword arguments
            callback: Called with loaded data
            
        Returns:
            Task ID
        """
        return self.submit_task(
            func=load_func,
            args=args,
            kwargs=kwargs,
            callback=callback,
            priority=TaskPriority.LOW
        )

    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending or running task.
        
        Args:
            task_id: ID of task to cancel
            
        Returns:
            True if task was cancelled, False otherwise
        """
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                              TaskStatus.CANCELLED):
                return False
            
            if task.future and not task.future.done():
                task.future.cancel()
            
            task.status = TaskStatus.CANCELLED
            self._total_cancelled += 1
            
            logger.debug(f"{self.name}: Task {task_id} cancelled")
            return True

    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """
        Get the current status of a task.
        
        Args:
            task_id: Task ID to query
            
        Returns:
            TaskStatus or None if task not found
        """
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            return task.status if task else None

    def get_task_result(self, task_id: str) -> Any:
        """
        Get the result of a completed task.
        
        Args:
            task_id: Task ID to query
            
        Returns:
            Task result if completed, None otherwise
            
        Raises:
            KeyError: If task not found
        """
        with self._tasks_lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError(f"Task {task_id} not found")
            return task.result

    def pause(self) -> None:
        """Pause task processing. Running tasks will complete."""
        if not self._running:
            logger.warning(f"{self.name}: Cannot pause, not running")
            return
        
        if self._paused:
            logger.warning(f"{self.name}: Already paused")
            return
        
        self._paused = True
        self._pause_event.clear()
        logger.info(f"{self.name}: Paused")

    def resume(self) -> None:
        """Resume task processing."""
        if not self._running:
            logger.warning(f"{self.name}: Cannot resume, not running")
            return
        
        if not self._paused:
            logger.warning(f"{self.name}: Not paused")
            return
        
        self._paused = False
        self._pause_event.set()
        logger.info(f"{self.name}: Resumed")

    def is_paused(self) -> bool:
        """Check if the manager is paused."""
        return self._paused

    def is_running(self) -> bool:
        """Check if the manager is running."""
        return self._running

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            Dictionary with statistics
        """
        with self._tasks_lock:
            return {
                "thread_count": self._thread_count,
                "total_submitted": self._total_submitted,
                "total_completed": self._total_completed,
                "total_failed": self._total_failed,
                "total_cancelled": self._total_cancelled,
                "pending_tasks": self._task_queue.qsize(),
                "active_tasks": len(self._active_tasks),
                "total_tasks": len(self._tasks),
                "is_running": self._running,
                "is_paused": self._paused
            }

    def get_pending_count(self) -> int:
        """Get number of pending tasks in queue."""
        return self._task_queue.qsize()

    def get_active_count(self) -> int:
        """Get number of currently executing tasks."""
        with self._tasks_lock:
            return len(self._active_tasks)

    def set_thread_count(self, thread_count: int) -> None:
        """
        Change the number of worker threads.
        
        This will restart the executor with the new thread count.
        Running tasks will complete before the restart.
        
        Args:
            thread_count: New thread count (1-16)
            
        Raises:
            ValueError: If thread_count is not in valid range
        """
        if not self.MIN_THREADS <= thread_count <= self.MAX_THREADS:
            raise ValueError(
                f"thread_count must be between {self.MIN_THREADS} and "
                f"{self.MAX_THREADS}, got {thread_count}"
            )

        if thread_count == self._thread_count:
            return

        logger.info(
            f"{self.name}: Changing thread count from {self._thread_count} "
            f"to {thread_count}"
        )
        
        was_running = self._running
        was_paused = self._paused
        
        if was_running:
            # Shutdown old executor
            if self._executor:
                self._executor.shutdown(wait=True)
                self._executor = None
            
            # Update thread count
            self._thread_count = thread_count
            
            # Create new executor
            self._executor = ThreadPoolExecutor(
                max_workers=self._thread_count,
                thread_name_prefix=f"{self.name}_Worker"
            )
            
            # Restore pause state
            if was_paused:
                self._pause_event.clear()
        else:
            self._thread_count = thread_count

    def clear_completed_tasks(self, older_than: Optional[float] = None) -> int:
        """
        Clear completed/failed/cancelled tasks from memory.
        
        Args:
            older_than: Only clear tasks older than this many seconds
            
        Returns:
            Number of tasks cleared
        """
        current_time = time.time()
        cleared_count = 0
        
        with self._tasks_lock:
            tasks_to_remove = []
            
            for task_id, task in self._tasks.items():
                if task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED,
                                      TaskStatus.CANCELLED):
                    continue
                
                if older_than is not None:
                    age = current_time - (task.completed_at or task.created_at)
                    if age < older_than:
                        continue
                
                tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self._tasks[task_id]
                cleared_count += 1
        
        if cleared_count > 0:
            logger.debug(f"{self.name}: Cleared {cleared_count} completed tasks")
        
        return cleared_count

    def _process_queue(self) -> None:
        """Internal method: Process tasks from the queue."""
        logger.debug(f"{self.name}: Queue worker started")
        
        while self._running or not self._task_queue.empty():
            try:
                # Wait for pause to clear
                self._pause_event.wait()
                
                # Check shutdown
                if not self._running and self._task_queue.empty():
                    break
                
                # Get task with timeout
                try:
                    task = self._task_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Check if task was cancelled while in queue
                with self._tasks_lock:
                    if task.status == TaskStatus.CANCELLED:
                        self._task_queue.task_done()
                        continue
                
                # Submit to executor
                if self._executor and self._running:
                    task.future = self._executor.submit(
                        self._execute_task,
                        task
                    )
                    with self._tasks_lock:
                        self._active_tasks.add(task.task_id)
                
                self._task_queue.task_done()
                
            except Exception as e:
                logger.error(f"{self.name}: Error in queue worker: {e}")
        
        logger.debug(f"{self.name}: Queue worker stopped")

    def _execute_task(self, task: Task) -> None:
        """Internal method: Execute a task and handle callbacks."""
        try:
            # Check if cancelled
            if task.status == TaskStatus.CANCELLED:
                return
            
            # Update status
            with self._tasks_lock:
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
            
            # Execute function
            result = task.func(*task.args, **task.kwargs)
            
            # Update status
            with self._tasks_lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                task.result = result
                self._total_completed += 1
                self._active_tasks.discard(task.task_id)
            
            # Call success callback
            if task.callback:
                try:
                    task.callback(result)
                except Exception as e:
                    logger.error(
                        f"{self.name}: Error in success callback for task "
                        f"{task.task_id}: {e}"
                    )
            
        except Exception as e:
            # Update status
            with self._tasks_lock:
                task.status = TaskStatus.FAILED
                task.completed_at = time.time()
                task.error = e
                self._total_failed += 1
                self._active_tasks.discard(task.task_id)
            
            logger.error(
                f"{self.name}: Task {task.task_id} failed: {e}",
                exc_info=True
            )
            
            # Call error callback
            if task.error_callback:
                try:
                    task.error_callback(e)
                except Exception as callback_error:
                    logger.error(
                        f"{self.name}: Error in error callback for task "
                        f"{task.task_id}: {callback_error}"
                    )

    def _cancel_pending_tasks(self) -> None:
        """Internal method: Cancel all pending tasks."""
        cancelled_count = 0
        
        with self._tasks_lock:
            for task in self._tasks.values():
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    cancelled_count += 1
        
        if cancelled_count > 0:
            logger.info(
                f"{self.name}: Cancelled {cancelled_count} pending tasks"
            )

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        return False

    def __del__(self):
        """Destructor: Ensure cleanup."""
        try:
            if self._running:
                self.shutdown(wait=False)
        except Exception:
            pass


    def stop(self, wait: bool = True) -> None:
        """Alias for shutdown(); stops all worker threads."""
        self.shutdown(wait=wait)
