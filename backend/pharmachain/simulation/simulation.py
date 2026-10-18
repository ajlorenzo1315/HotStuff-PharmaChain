"""Observable controller for the existing HotStuffEngine.

One step executes one complete consensus view.
This is not yet a message-by-message network simulator.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pharmachain.consensus.engine import HotStuffEngine
from pharmachain.domain.state import LedgerState
from pharmachain.domain.transactions import Transaction
from pharmachain.engines.events import ConsensusEvent, EventType


@dataclass
class Simulation:
    initial_state: LedgerState
    validator_count: int = 4

    engine: HotStuffEngine = field(init=False)

    events: list[ConsensusEvent] = field(
        default_factory=list,
        init=False,
    )

    def __post_init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        """Restart the simulation."""
        self.engine = HotStuffEngine(
            self.initial_state.clone(),
            self.validator_count,
        )
        self.events = []

    def set_active(
        self,
        validator_id: str,
        active: bool,
    ) -> None:
        """Enable or disable a validator."""
        for validator in self.engine.validators:
            if validator.validator_id == validator_id:
                validator.active = active
                return

        raise ValueError(f"Unknown validator: {validator_id}")

    def _event(
        self,
        kind: EventType,
        view: int,
        message: str,
        block_hash: str | None = None,
        validator_id: str | None = None,
        **details: object,
    ) -> ConsensusEvent:
        return ConsensusEvent(
            kind,
            "python-hotstuff",
            view,
            block_hash,
            validator_id,
            message,
            details,
        )

    def step(
        self,
        transactions: list[Transaction] | None = None,
    ) -> list[ConsensusEvent]:
        """Execute one view and record its events."""

        view = self.engine.view
        leader = self.engine.leader()

        was_active = leader.active

        previous_votes = {validator.validator_id: set(validator.voted_views) for validator in self.engine.validators}

        result = self.engine.run_round(transactions)

        produced = [
            self._event(
                EventType.VIEW_CHANGED,
                view,
                f"Leader selected: {result.leader}",
                validator_id=result.leader,
            )
        ]

        if not was_active:
            produced.append(
                self._event(
                    EventType.TIMEOUT,
                    view,
                    "Leader inactive; view skipped",
                    validator_id=result.leader,
                )
            )

        else:
            produced.append(
                self._event(
                    EventType.BLOCK_PROPOSED,
                    view,
                    "Leader proposed a block",
                    block_hash=result.block_hash,
                    validator_id=result.leader,
                )
            )

            for validator in self.engine.validators:
                voted_now = view in validator.voted_views and view not in previous_votes[validator.validator_id]

                if voted_now:
                    produced.append(
                        self._event(
                            EventType.VOTE_CAST,
                            view,
                            "Validator signed its vote",
                            block_hash=result.block_hash,
                            validator_id=validator.validator_id,
                        )
                    )

            if result.qc_formed:
                produced.append(
                    self._event(
                        EventType.QC_FORMED,
                        view,
                        "Quorum certificate verified",
                        block_hash=result.block_hash,
                        votes=result.votes,
                        quorum=self.engine.quorum,
                    )
                )

            else:
                produced.append(
                    self._event(
                        EventType.TIMEOUT,
                        view,
                        "Quorum not reached",
                        block_hash=result.block_hash,
                        votes=result.votes,
                        quorum=self.engine.quorum,
                    )
                )

            for committed_hash in result.committed:
                produced.append(
                    self._event(
                        EventType.BLOCK_COMMITTED,
                        view,
                        "Block committed by three-chain rule",
                        block_hash=committed_hash,
                    )
                )

        self.events.extend(produced)

        return produced

    def snapshot(self) -> dict:
        """Return the current simulation state."""

        chain = self.engine.blockchain

        return {
            "view": self.engine.view,
            "f": self.engine.f,
            "quorum": self.engine.quorum,
            "leader": self.engine.leader().validator_id,
            "high_qc_hash": self.engine.high_qc_hash,
            "validators": [
                {
                    "id": validator.validator_id,
                    "active": validator.active,
                    "locked_block_hash": (validator.locked_block_hash),
                    "locked_view": validator.locked_view,
                    "voted_views": sorted(validator.voted_views),
                }
                for validator in self.engine.validators
            ],
            "blocks": [
                {
                    "hash": block_hash,
                    "parent": (block.parent_hash if block.height else None),
                    "height": block.height,
                    "view": block.view,
                    "proposer": block.proposer_id,
                    "transactions": len(block.transactions),
                    "certified": (block_hash in self.engine.certificates),
                    "committed": chain.is_committed(block_hash),
                }
                for block_hash, block in sorted(
                    chain.blocks.items(),
                    key=lambda item: (
                        item[1].height,
                        item[1].view,
                    ),
                )
            ],
            "events": [event.to_dict() for event in self.events],
        }
