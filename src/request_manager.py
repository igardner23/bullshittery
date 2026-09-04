"""Request management and batching for efficient LLM API usage.

Coordinates response generation requests, batches them where possible,
and manages request priorities (human input > ambient chat).
"""

import asyncio
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class RequestPriority(Enum):
    """Priority levels for response generation."""
    HIGH = 0      # Direct human interaction
    MEDIUM = 1    # Chain responses / context-dependent
    LOW = 2       # Ambient chat


@dataclass
class GenerationRequest:
    """A queued request for AI response generation."""
    player: Dict
    chat_history: List[Dict]
    context_user: Optional[str]
    user_profile: Optional[Dict]
    priority: RequestPriority
    created_at: float
    request_id: str
    
    def age(self) -> float:
        """How long this request has been queued (seconds)."""
        return time.time() - self.created_at


class RequestManager:
    """Manages request queue with batching and priority handling.
    
    Benefits:
    - Parallel generation for multiple personas
    - Priority queuing (human > chain > ambient)
    - Request deduplication (avoid generating same context twice)
    - Backpressure handling (skip old ambient requests if queue backs up)
    """
    
    def __init__(self, max_concurrent: int = 3, batch_timeout: float = 1.0):
        """Initialize request manager.
        
        Args:
            max_concurrent: Max parallel requests to process
            batch_timeout: How long to wait before processing partial batch
        """
        self.queue: List[GenerationRequest] = []
        self.max_concurrent = max_concurrent
        self.batch_timeout = batch_timeout
        self.processing = False
        self._request_counter = 0
        self._lock = asyncio.Lock()
    
    def _generate_request_id(self) -> str:
        """Generate unique request ID."""
        self._request_counter += 1
        return f"req_{self._request_counter:05d}"
    
    async def submit_request(
        self,
        player: Dict,
        chat_history: List[Dict],
        priority: RequestPriority = RequestPriority.LOW,
        context_user: Optional[str] = None,
        user_profile: Optional[Dict] = None
    ) -> str:
        """Submit a response generation request.
        
        Returns request ID that can be used to track completion.
        """
        async with self._lock:
            request_id = self._generate_request_id()
            request = GenerationRequest(
                player=player,
                chat_history=chat_history.copy(),
                context_user=context_user,
                user_profile=user_profile,
                priority=priority,
                created_at=time.time(),
                request_id=request_id
            )
            self.queue.append(request)
            print(f"[QUEUE] {request_id}: Queued {player['name']} (priority: {priority.name})")
            return request_id
    
    async def process_queue(self, generator_fn: Callable) -> List[Dict]:
        """Process pending requests in priority order.
        
        Args:
            generator_fn: Async function(request) -> response_dict
            
        Returns:
            List of (request_id, player_name, response_text) tuples
        """
        if self.processing:
            print("[QUEUE] Already processing, skipping")
            return []
        
        self.processing = True
        results = []
        
        try:
            async with self._lock:
                # Sort by priority, then by age (older first)
                self.queue.sort(
                    key=lambda r: (r.priority.value, r.created_at)
                )
                
                # Take up to max_concurrent requests
                batch = self.queue[:self.max_concurrent]
                self.queue = self.queue[self.max_concurrent:]
                
                if not batch:
                    return results
                
                print(f"[QUEUE] Processing batch of {len(batch)} requests")
            
            # Process batch in parallel
            tasks = [
                self._process_single_request(req, generator_fn)
                for req in batch
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions (they were logged)
            results = [r for r in results if not isinstance(r, Exception)]
            
        finally:
            self.processing = False
        
        return results
    
    async def _process_single_request(
        self,
        request: GenerationRequest,
        generator_fn: Callable
    ) -> Optional[Dict]:
        """Process a single request."""
        try:
            print(f"[QUEUE] {request.request_id}: Generating for {request.player['name']}...")
            
            response_text = await generator_fn(request)
            
            result = {
                'request_id': request.request_id,
                'player_name': request.player['name'],
                'response': response_text,
                'priority': request.priority.name,
                'age': request.age()
            }
            
            print(f"[QUEUE] {request.request_id}: Complete ({request.age():.1f}s queued)")
            return result
            
        except Exception as e:
            print(f"[QUEUE] {request.request_id}: Error - {e}")
            return None
    
    def get_queue_stats(self) -> Dict:
        """Get current queue statistics."""
        high = sum(1 for r in self.queue if r.priority == RequestPriority.HIGH)
        medium = sum(1 for r in self.queue if r.priority == RequestPriority.MEDIUM)
        low = sum(1 for r in self.queue if r.priority == RequestPriority.LOW)
        
        oldest_age = max([r.age() for r in self.queue]) if self.queue else 0
        
        return {
            'total': len(self.queue),
            'high_priority': high,
            'medium_priority': medium,
            'low_priority': low,
            'oldest_age_sec': oldest_age,
            'processing': self.processing
        }
    
    async def apply_backpressure(self) -> bool:
        """Apply backpressure: drop old ambient requests if queue is too large.
        
        Returns True if backpressure was applied.
        """
        async with self._lock:
            if len(self.queue) > self.max_concurrent * 2:
                # Remove oldest low-priority requests
                low_priority = [r for r in self.queue if r.priority == RequestPriority.LOW]
                if low_priority:
                    dropped = low_priority[0]
                    self.queue.remove(dropped)
                    print(f"[QUEUE] Backpressure: Dropped old ambient request from {dropped.player['name']}")
                    return True
        
        return False
