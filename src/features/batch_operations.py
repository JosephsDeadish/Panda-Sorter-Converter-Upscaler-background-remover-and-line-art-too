"""
Batch Operations System
Queue and manage batch operations with progress tracking
Author: Dead On The Inside / JosephsDeadish
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from threading import Thread, Lock, Event
from queue import PriorityQueue, Empty
import traceback

logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """Status of a batch operation."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OperationPriority(Enum):
    """Priority levels for operations."""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class Operation:
    """Represents a single batch operation."""
    id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: OperationPriority = OperationPriority.NORMAL
    status: OperationStatus = OperationStatus.PENDING
    progress: float = 0.0
    result: Any = None
    error: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    def __lt__(self, other):
        """Compare operations by priority for priority queue."""
        return self.priority.value < other.priority.value


@dataclass
class OperationHistory:
    """History record of a completed operation."""
    operation_id: str
    name: str
    status: OperationStatus
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration: float
    error: Optional[str] = None
    result_summary: Optional[str] = None


class BatchQueue:
    """
    Batch operation queue with priority management.
    
    Features:
    - Queue multiple operations with priority levels
    - Pause/resume operations
    - Cancel individual operations
    - Progress tracking per operation
    - Operation history
    - Thread-safe execution
    - Error handling and recovery
    """
    
    def __init__(self, max_history: int = 100):
        """
        Initialize batch queue.
        
        Args:
            max_history: Maximum number of history records to keep
        """
        self.queue: PriorityQueue = PriorityQueue()
        self.operations: Dict[str, Operation] = {}
        self.history: List[OperationHistory] = []
        self.max_history = max_history
        
        self._lock = Lock()
        self._worker_thread: Optional[Thread] = None
        self._running = Event()
        self._paused = Event()
        self._current_operation: Optional[Operation] = None
        self._operation_counter = 0
        
        logger.debug(f"BatchQueue initialized with max_history={max_history}")
    
    def add_operation(
        self,
        name: str,
        function: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: OperationPriority = OperationPriority.NORMAL
    ) -> str:
        """
        Add an operation to the queue.
        
        Args:
            name: Operation name/description
            function: Function to execute
            args: Positional arguments for function
            kwargs: Keyword arguments for function
            priority: Operation priority
            
        Returns:
            Operation ID
        """
        try:
            with self._lock:
                self._operation_counter += 1
                operation_id = f"op_{self._operation_counter}_{int(time.time())}"
                
                operation = Operation(
                    id=operation_id,
                    name=name,
                    function=function,
                    args=args,
                    kwargs=kwargs or {},
                    priority=priority
                )
                
                self.operations[operation_id] = operation
                self.queue.put((priority.value, operation))
                
                logger.info(f"Added operation: {name} (ID: {operation_id}, Priority: {priority.name})")
                return operation_id
                
        except Exception as e:
            logger.error(f"Error adding operation '{name}': {e}", exc_info=True)
            raise
    
    def start(self):
        """Start processing the queue."""
        with self._lock:
            if self._running.is_set():
                logger.warning("Queue is already running")
                return
            
            self._running.set()
            self._paused.clear()
            
            if self._worker_thread is None or not self._worker_thread.is_alive():
                self._worker_thread = Thread(target=self._process_queue, daemon=True)
                self._worker_thread.start()
                logger.info("Started batch queue processing")
    
    def pause(self):
        """Pause queue processing (current operation will finish)."""
        if not self._running.is_set():
            logger.warning("Queue is not running")
            return
        
        self._paused.set()
        logger.info("Paused batch queue")
    
    def resume(self):
        """Resume queue processing."""
        if not self._running.is_set():
            logger.warning("Queue is not running")
            return
        
        self._paused.clear()
        logger.info("Resumed batch queue")
    
    def stop(self, wait: bool = True):
        """
        Stop queue processing.
        
        Args:
            wait: Whether to wait for current operation to finish
        """
        self._running.clear()
        self._paused.clear()
        
        if wait and self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=10)
        
        logger.info("Stopped batch queue")
    
    def cancel_operation(self, operation_id: str) -> bool:
        """
        Cancel a pending operation.
        
        Args:
            operation_id: ID of operation to cancel
            
        Returns:
            True if cancelled, False if not found or already running/completed
        """
        try:
            with self._lock:
                if operation_id not in self.operations:
                    logger.warning(f"Operation not found: {operation_id}")
                    return False
                
                operation = self.operations[operation_id]
                
                if operation.status == OperationStatus.PENDING:
                    operation.status = OperationStatus.CANCELLED
                    operation.completed_at = datetime.now().isoformat()
                    self._add_to_history(operation)
                    logger.info(f"Cancelled operation: {operation_id}")
                    return True
                elif operation.status == OperationStatus.RUNNING:
                    # Mark for cancellation (operation must check this)
                    operation.status = OperationStatus.CANCELLED
                    logger.info(f"Marked running operation for cancellation: {operation_id}")
                    return True
                else:
                    logger.warning(f"Cannot cancel operation in state {operation.status}: {operation_id}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error cancelling operation {operation_id}: {e}", exc_info=True)
            return False
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of an operation.
        
        Args:
            operation_id: Operation ID
            
        Returns:
            Dictionary with operation status or None if not found
        """
        with self._lock:
            if operation_id not in self.operations:
                return None
            
            operation = self.operations[operation_id]
            return {
                'id': operation.id,
                'name': operation.name,
                'status': operation.status.value,
                'priority': operation.priority.name,
                'progress': operation.progress,
                'created_at': operation.created_at,
                'started_at': operation.started_at,
                'completed_at': operation.completed_at,
                'error': operation.error
            }
    
    def get_all_operations(self) -> List[Dict[str, Any]]:
        """
        Get status of all operations.
        
        Returns:
            List of operation status dictionaries
        """
        with self._lock:
            return [
                self.get_operation_status(op_id)
                for op_id in self.operations.keys()
            ]
    
    def get_queue_size(self) -> int:
        """
        Get number of pending operations.
        
        Returns:
            Number of operations in queue
        """
        return self.queue.qsize()
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get operation history.
        
        Args:
            limit: Maximum number of history records to return
            
        Returns:
            List of history records
        """
        with self._lock:
            history = self.history[-limit:] if limit else self.history
            return [
                {
                    'operation_id': record.operation_id,
                    'name': record.name,
                    'status': record.status.value,
                    'created_at': record.created_at,
                    'started_at': record.started_at,
                    'completed_at': record.completed_at,
                    'duration': record.duration,
                    'error': record.error,
                    'result_summary': record.result_summary
                }
                for record in history
            ]
    
    def clear_history(self):
        """Clear operation history."""
        with self._lock:
            self.history.clear()
            logger.info("Cleared operation history")
    
    def get_current_operation(self) -> Optional[Dict[str, Any]]:
        """
        Get currently running operation.
        
        Returns:
            Operation status dictionary or None
        """
        with self._lock:
            if self._current_operation:
                return self.get_operation_status(self._current_operation.id)
            return None
    
    def is_running(self) -> bool:
        """Check if queue is running."""
        return self._running.is_set()
    
    def is_paused(self) -> bool:
        """Check if queue is paused."""
        return self._paused.is_set()
    
    def _process_queue(self):
        """Worker thread to process operations from queue."""
        logger.debug("Queue worker thread started")
        
        while self._running.is_set():
            try:
                # Wait if paused
                while self._paused.is_set() and self._running.is_set():
                    time.sleep(0.1)
                
                if not self._running.is_set():
                    break
                
                # Get next operation (with timeout to allow checking _running)
                try:
                    priority, operation = self.queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Check if operation was cancelled
                if operation.status == OperationStatus.CANCELLED:
                    logger.debug(f"Skipping cancelled operation: {operation.id}")
                    self.queue.task_done()
                    continue
                
                # Execute operation
                self._execute_operation(operation)
                self.queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in queue worker: {e}", exc_info=True)
                time.sleep(1)
        
        logger.debug("Queue worker thread stopped")
    
    def _execute_operation(self, operation: Operation):
        """
        Execute a single operation.
        
        Args:
            operation: Operation to execute
        """
        start_time = time.time()
        
        with self._lock:
            self._current_operation = operation
            operation.status = OperationStatus.RUNNING
            operation.started_at = datetime.now().isoformat()
        
        logger.info(f"Executing operation: {operation.name} (ID: {operation.id})")
        
        try:
            # Execute the operation
            result = operation.function(*operation.args, **operation.kwargs)
            
            # Check if cancelled during execution
            if operation.status == OperationStatus.CANCELLED:
                logger.info(f"Operation was cancelled during execution: {operation.id}")
            else:
                operation.status = OperationStatus.COMPLETED
                operation.result = result
                operation.progress = 100.0
                logger.info(f"Completed operation: {operation.name} (ID: {operation.id})")
            
        except Exception as e:
            operation.status = OperationStatus.FAILED
            operation.error = str(e)
            logger.error(
                f"Operation failed: {operation.name} (ID: {operation.id})\n"
                f"Error: {e}\n"
                f"Traceback: {traceback.format_exc()}"
            )
        
        finally:
            duration = time.time() - start_time
            operation.completed_at = datetime.now().isoformat()
            
            with self._lock:
                self._current_operation = None
            
            # Add to history
            self._add_to_history(operation, duration)
    
    def _add_to_history(self, operation: Operation, duration: float = 0.0):
        """
        Add operation to history.
        
        Args:
            operation: Completed operation
            duration: Operation duration in seconds
        """
        try:
            with self._lock:
                # Create summary of result
                result_summary = None
                if operation.result is not None:
                    result_str = str(operation.result)
                    result_summary = result_str[:200] + "..." if len(result_str) > 200 else result_str
                
                history_record = OperationHistory(
                    operation_id=operation.id,
                    name=operation.name,
                    status=operation.status,
                    created_at=operation.created_at,
                    started_at=operation.started_at,
                    completed_at=operation.completed_at,
                    duration=duration,
                    error=operation.error,
                    result_summary=result_summary
                )
                
                self.history.append(history_record)
                
                # Trim history if needed
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]
                
                logger.debug(f"Added operation to history: {operation.id}")
                
        except Exception as e:
            logger.error(f"Error adding operation to history: {e}", exc_info=True)
    
    def update_operation_progress(self, operation_id: str, progress: float):
        """
        Update progress of a running operation.
        
        Args:
            operation_id: Operation ID
            progress: Progress percentage (0-100)
        """
        with self._lock:
            if operation_id in self.operations:
                self.operations[operation_id].progress = max(0.0, min(100.0, progress))


class BatchOperationHelper:
    """
    Helper class with common batch operations.
    """
    
    @staticmethod
    def batch_copy_files(
        files: List[Path],
        destination: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Batch copy files to destination.
        
        Args:
            files: List of source files
            destination: Destination directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with operation results
        """
        import shutil
        
        destination.mkdir(parents=True, exist_ok=True)
        
        copied = []
        failed = []
        
        for i, file_path in enumerate(files):
            try:
                dest_file = destination / file_path.name
                shutil.copy2(file_path, dest_file)
                copied.append(file_path)
                
                if progress_callback:
                    progress = (i + 1) / len(files) * 100
                    progress_callback(progress)
                    
            except Exception as e:
                logger.error(f"Failed to copy {file_path}: {e}")
                failed.append((file_path, str(e)))
        
        return {
            'copied': len(copied),
            'failed': len(failed),
            'failed_files': failed
        }
    
    @staticmethod
    def batch_move_files(
        files: List[Path],
        destination: Path,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Batch move files to destination.
        
        Args:
            files: List of source files
            destination: Destination directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with operation results
        """
        import shutil
        
        destination.mkdir(parents=True, exist_ok=True)
        
        moved = []
        failed = []
        
        for i, file_path in enumerate(files):
            try:
                dest_file = destination / file_path.name
                shutil.move(str(file_path), str(dest_file))
                moved.append(file_path)
                
                if progress_callback:
                    progress = (i + 1) / len(files) * 100
                    progress_callback(progress)
                    
            except Exception as e:
                logger.error(f"Failed to move {file_path}: {e}")
                failed.append((file_path, str(e)))
        
        return {
            'moved': len(moved),
            'failed': len(failed),
            'failed_files': failed
        }
    
    @staticmethod
    def batch_delete_files(
        files: List[Path],
        use_trash: bool = True,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> Dict[str, Any]:
        """
        Batch delete files.
        
        Args:
            files: List of files to delete
            use_trash: Send to trash instead of permanent deletion
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with operation results
        """
        try:
            from send2trash import send2trash
            HAS_SEND2TRASH = True
        except ImportError:
            HAS_SEND2TRASH = False
            logger.warning("send2trash not available, using permanent deletion")
        
        deleted = []
        failed = []
        
        for i, file_path in enumerate(files):
            try:
                if use_trash and HAS_SEND2TRASH:
                    send2trash(str(file_path))
                elif use_trash and not HAS_SEND2TRASH:
                    logger.warning(f"send2trash unavailable, permanently deleting {file_path}")
                    file_path.unlink()
                else:
                    file_path.unlink()
                
                deleted.append(file_path)
                
                if progress_callback:
                    progress = (i + 1) / len(files) * 100
                    progress_callback(progress)
                    
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {e}")
                failed.append((file_path, str(e)))
        
        return {
            'deleted': len(deleted),
            'failed': len(failed),
            'failed_files': failed
        }
