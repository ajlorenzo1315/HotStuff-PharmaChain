"""Deterministic event-driven network for educational HotStuff simulations.

Transport only: this module does not validate signatures or form QCs.
"""

from __future__ import annotations

import heapq
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Envelope:
    sender: str
    recipient: str
    kind: str
    payload: Any
    message_id: int


@dataclass(order=True)
class ScheduledDelivery:
    deliver_at: float
    sequence: int
    envelope: Envelope = field(compare=False)


@dataclass(frozen=True)
class NetworkEvent:
    at: float
    action: str
    message_id: int
    sender: str
    recipient: str
    kind: str


class SimulatedNetwork:
    def __init__(self, *, latency: float = 0.1, loss_rate: float = 0.0, seed: int = 42) -> None:
        if latency < 0:
            raise ValueError("latency must be nonnegative")
        if not 0 <= loss_rate <= 1:
            raise ValueError("loss_rate must be between 0 and 1")
        self.time = 0.0
        self.latency = latency
        self.loss_rate = loss_rate
        self._random = random.Random(seed)
        self._handlers: dict[str, Callable[[Envelope], None]] = {}
        self._queue: list[ScheduledDelivery] = []
        self._next_id = 0
        self._sequence = 0
        self.offline: set[str] = set()
        self.blocked_links: set[tuple[str, str]] = set()
        self.events: list[NetworkEvent] = []

    def register(self, node_id: str, handler: Callable[[Envelope], None]) -> None:
        if node_id in self._handlers:
            raise ValueError(f"duplicate node: {node_id}")
        self._handlers[node_id] = handler

    def disconnect(self, node_id: str) -> None:
        self.offline.add(node_id)

    def reconnect(self, node_id: str) -> None:
        self.offline.discard(node_id)

    def partition(self, groups: list[set[str]]) -> None:
        """Block both directions between nodes in different groups."""
        if len(set().union(*groups)) != sum(map(len, groups)):
            raise ValueError("partition groups must be disjoint")
        self.blocked_links.clear()
        for i, group in enumerate(groups):
            for other in groups[i + 1 :]:
                for a in group:
                    for b in other:
                        self.blocked_links.add((a, b))
                        self.blocked_links.add((b, a))

    def heal(self) -> None:
        self.blocked_links.clear()

    def _log(self, action: str, msg: Envelope) -> None:
        self.events.append(NetworkEvent(self.time, action, msg.message_id, msg.sender, msg.recipient, msg.kind))

    def send(
        self,
        sender: str,
        recipient: str,
        kind: str,
        payload: Any,
        *,
        delay: float | None = None,
        copies: int = 1,
    ) -> list[int]:
        if sender not in self._handlers or recipient not in self._handlers:
            raise ValueError("sender and recipient must be registered")
        if delay is not None and delay < 0:
            raise ValueError("delay must be nonnegative")
        if copies < 1:
            raise ValueError("copies must be positive")
        ids = []
        for _ in range(copies):
            self._next_id += 1
            msg = Envelope(sender, recipient, kind, payload, self._next_id)
            ids.append(msg.message_id)
            self._log("SENT", msg)
            if (
                sender in self.offline
                or recipient in self.offline
                or (sender, recipient) in self.blocked_links
                or self._random.random() < self.loss_rate
            ):
                self._log("DROPPED", msg)
                continue
            self._sequence += 1
            heapq.heappush(
                self._queue,
                ScheduledDelivery(
                    self.time + (self.latency if delay is None else delay),
                    self._sequence,
                    msg,
                ),
            )
        return ids

    def broadcast(self, sender: str, kind: str, payload: Any, *, include_sender: bool = False) -> None:
        for recipient in self._handlers:
            if include_sender or recipient != sender:
                self.send(sender, recipient, kind, payload)

    def run(self, *, until: float | None = None, max_events: int = 10000) -> int:
        if until is not None and until < self.time:
            raise ValueError("until must not be earlier than current time")
        processed = 0
        while self._queue and processed < max_events:
            if until is not None and self._queue[0].deliver_at > until:
                break
            event = heapq.heappop(self._queue)
            self.time = event.deliver_at
            msg = event.envelope
            if msg.sender in self.offline or msg.recipient in self.offline or (msg.sender, msg.recipient) in self.blocked_links:
                self._log("DROPPED", msg)
            else:
                self._log("DELIVERED", msg)
                self._handlers[msg.recipient](msg)
            processed += 1
        if until is not None:
            self.time = until
        return processed

    @property
    def pending(self) -> int:
        return len(self._queue)
