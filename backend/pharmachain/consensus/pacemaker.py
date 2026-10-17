"""Deterministic local pacemaker for educational HotStuff simulations."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimeoutNotice:
    validator_id: str
    view: int


@dataclass(frozen=True)
class TimeoutCertificate:
    view: int
    signers: frozenset[str]


class Pacemaker:
    def __init__(
        self,
        validator_ids: list[str],
        timeout: float = 2.0,
    ):
        if len(validator_ids) < 4 or len(set(validator_ids)) != len(validator_ids):
            raise ValueError("Need at least four unique validators")

        if timeout <= 0:
            raise ValueError("Timeout must be positive")

        self.validator_ids = tuple(validator_ids)
        self.f = (len(validator_ids) - 1) // 3
        self.quorum = len(validator_ids) - self.f
        self.timeout = timeout

        self.view = {node: 1 for node in validator_ids}
        self.deadline = {node: timeout for node in validator_ids}

        self.sent: set[tuple[str, int]] = set()
        self.notices: dict[int, set[str]] = {}
        self.certificates: dict[int, TimeoutCertificate] = {}

        self.events: list[dict] = []

    def leader(self, view: int) -> str:
        if view < 1:
            raise ValueError("View must be positive")

        return self.validator_ids[(view - 1) % len(self.validator_ids)]

    def tick(
        self,
        now: float,
        online: set[str],
    ) -> list[TimeoutNotice]:
        emitted = []

        for node in self.validator_ids:
            if node not in online:
                continue

            view = self.view[node]

            if now >= self.deadline[node] and (node, view) not in self.sent:
                self.sent.add((node, view))

                notice = TimeoutNotice(node, view)
                emitted.append(notice)

                self.events.append(
                    {
                        "time": now,
                        "event": "TIMEOUT",
                        "node": node,
                        "view": view,
                    }
                )

        return emitted

    def receive_timeout(
        self,
        notice: TimeoutNotice,
        now: float,
    ) -> TimeoutCertificate | None:
        if notice.validator_id not in self.view or notice.view < 1:
            return None

        voters = self.notices.setdefault(notice.view, set())
        voters.add(notice.validator_id)

        if len(voters) < self.quorum:
            return None

        if notice.view in self.certificates:
            return None

        tc = TimeoutCertificate(
            notice.view,
            frozenset(voters),
        )

        self.certificates[notice.view] = tc

        self.events.append(
            {
                "time": now,
                "event": "TC_FORMED",
                "view": notice.view,
                "signers": sorted(tc.signers),
            }
        )

        return tc

    def advance(
        self,
        node: str,
        tc: TimeoutCertificate,
        now: float,
    ) -> bool:
        if node not in self.view or tc.view not in self.certificates:
            return False

        if tc != self.certificates[tc.view]:
            return False

        if len(tc.signers) < self.quorum or not tc.signers.issubset(self.view):
            return False

        if tc.view + 1 <= self.view[node]:
            return False

        self.view[node] = tc.view + 1
        self.deadline[node] = now + self.timeout

        self.events.append(
            {
                "time": now,
                "event": "VIEW_CHANGED",
                "node": node,
                "view": self.view[node],
            }
        )

        return True

    def on_progress(
        self,
        node: str,
        view: int,
        now: float,
    ) -> None:
        if node not in self.view:
            raise ValueError("Unknown node")

        if view < self.view[node]:
            return

        self.view[node] = view + 1
        self.deadline[node] = now + self.timeout

        self.events.append(
            {
                "time": now,
                "event": "PROGRESS",
                "node": node,
                "view": view,
            }
        )
