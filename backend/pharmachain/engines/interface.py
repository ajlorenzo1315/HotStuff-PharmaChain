from dataclasses import dataclass
from typing import Protocol

from pharmachain.domain.transactions import Transaction
from pharmachain.engines.events import ConsensusEvent


@dataclass(frozen=True)
class EngineCapabilities:
    step_by_step: bool
    internal_votes: bool
    byzantine_faults: bool
    adaptive_pacemaker: bool
    real_network: bool
    smart_contracts: bool


class ConsensusEngine(Protocol):
    name: str
    capabilities: EngineCapabilities

    def submit(self, tx: Transaction) -> str:
        """Submit a transaction to the engine."""
        ...

    def step(self) -> list[ConsensusEvent]:
        """Advance one simulation step, if supported."""
        ...

    def snapshot(self) -> dict:
        """Return current observable state."""
        ...

    def reset(self) -> None:
        """Reset the engine to its initial state."""
        ...
