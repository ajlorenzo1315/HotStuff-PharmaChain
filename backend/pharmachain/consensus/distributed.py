"""Simulador educativo de Chained HotStuff.

Los nodos poseen estado independiente y se comunican
mediante mensajes de una red simulada.

No implementa todavía pacemaker ni sincronización
de nodos que se incorporan tarde.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pharmachain.blockchain.block import Block
from pharmachain.consensus.messages import (
    QuorumCertificate,
    Vote,
)
from pharmachain.consensus.new_view import NewView, NewViewCollector
from pharmachain.consensus.node import HotStuffNode
from pharmachain.consensus.validator import Validator
from pharmachain.consensus.view_change import SignedTimeout, TimeoutCertificate
from pharmachain.domain.state import LedgerState
from pharmachain.simulation.network import (
    Envelope,
    SimulatedNetwork,
)


@dataclass(frozen=True)
class Proposal:
    block: Block
    justify: QuorumCertificate | None


@dataclass(frozen=True)
class RoundResult:
    view: int
    leader: str
    block_hash: str | None
    votes: int
    qc_formed: bool
    committed_heights: dict[str, int]


@dataclass
class NodeRuntime:
    node: HotStuffNode

    votes: dict[
        tuple[int, str],
        dict[str, Vote],
    ] = field(default_factory=dict)

    proposed: dict[int, str] = field(default_factory=dict)

    formed_qcs: set[tuple[int, str]] = field(default_factory=set)
    timeouts: dict[int, dict[str, SignedTimeout]] = field(default_factory=dict)
    formed_tcs: set[int] = field(default_factory=set)
    new_views: dict[int, NewViewCollector] = field(default_factory=dict)


class DistributedHotStuff:
    def __init__(
        self,
        initial_state: LedgerState,
        validator_count: int = 4,
        latency: float = 0.1,
        seed: int = 42,
    ):
        if validator_count < 4:
            raise ValueError("At least four validators required")

        # El valor 2f+1 sigue siendo correcto cuando n=3f+1,
        # como sucede con tus cuatro validadores.
        self.f = (validator_count - 1) // 3
        self.quorum = validator_count - self.f

        self.view = 1

        self.network = SimulatedNetwork(
            latency=latency,
            seed=seed,
        )

        validators = [
            Validator.create(f"validator-{i}") for i in range(validator_count)
        ]

        self.public_keys = {v.validator_id: v.public_key for v in validators}

        self.nodes: dict[str, NodeRuntime] = {}
        self.events: list[dict] = []

        for validator in validators:
            node = HotStuffNode.create(
                validator=validator,
                initial_state=initial_state,
                public_keys=self.public_keys,
                quorum=self.quorum,
            )

            self.nodes[validator.validator_id] = NodeRuntime(node=node)

            self.network.register(
                validator.validator_id,
                lambda msg, nid=validator.validator_id: self._receive(nid, msg),
            )

        self.genesis_hash = next(
            iter(self.nodes.values())
        ).node.blockchain.genesis.block_hash

    def _record(self, event: str, **details) -> None:
        self.events.append(
            {
                "time": self.network.time,
                "event": event,
                **details,
            }
        )

    def leader_id(self, view: int) -> str:
        index = (view - 1) % len(self.nodes)
        return f"validator-{index}"

    def _receive(self, recipient: str, msg: Envelope) -> None:
        if msg.kind == "PROPOSE":
            self._on_proposal(recipient, msg)
        elif msg.kind == "VOTE":
            self._on_vote(recipient, msg)
        elif msg.kind == "QC":
            self._on_qc(recipient, msg)
        elif msg.kind == "TIMEOUT":
            self._on_timeout(recipient, msg)
        elif msg.kind == "TC":
            self._on_tc(recipient, msg)
        elif msg.kind == "NEW_VIEW":
            self._on_new_view(recipient, msg)

    def _on_proposal(
        self,
        recipient: str,
        msg: Envelope,
    ) -> None:
        runtime = self.nodes[recipient]
        node = runtime.node

        if not isinstance(msg.payload, Proposal):
            return

        proposal = msg.payload
        block = proposal.block
        justify = proposal.justify

        # Solo el líder autorizado puede proponer.
        if msg.sender != self.leader_id(block.view):
            self._record(
                "REJECT_LEADER",
                node=recipient,
                view=block.view,
            )
            return

        if block.proposer_id != msg.sender:
            return

        if block.view != node.view:
            return

        if block.view in node.validator.voted_views:
            self._record(
                "DOUBLE_VOTE_PREVENTED",
                node=recipient,
                view=block.view,
            )
            return

        # La propuesta debe justificar exactamente al padre.
        if justify is None:
            if block.parent_hash != self.genesis_hash:
                return
        else:
            if justify.block_hash != block.parent_hash:
                return

            if not justify.verify(
                self.public_keys,
                self.quorum,
            ):
                return

            parent = node.blockchain.blocks.get(block.parent_hash)

            if parent is None or parent.view != justify.view:
                self._record(
                    "MISSING_PARENT",
                    node=recipient,
                    view=block.view,
                )
                return

        if not node.is_safe(block.parent_hash, justify):
            self._record(
                "UNSAFE_PROPOSAL",
                node=recipient,
                view=block.view,
            )
            return

        if not node.receive_block(block):
            return

        # El certificado justificativo es conocimiento local.
        if justify is not None:
            node.receive_qc(justify)

        vote = node.validator.vote(
            view=block.view,
            block_hash=block.block_hash,
            safe=True,
        )

        if vote is None:
            return

        self._record(
            "VOTE_CREATED",
            node=recipient,
            view=block.view,
            block=block.block_hash,
        )

        self.network.send(
            recipient,
            msg.sender,
            "VOTE",
            vote,
        )

    def _on_vote(
        self,
        recipient: str,
        msg: Envelope,
    ) -> None:
        runtime = self.nodes[recipient]

        if not isinstance(msg.payload, Vote):
            return

        vote = msg.payload

        if recipient != self.leader_id(vote.view):
            return

        if msg.sender != vote.validator_id:
            return

        key = self.public_keys.get(vote.validator_id)

        if key is None or not vote.verify(key):
            self._record(
                "INVALID_VOTE",
                node=recipient,
                sender=msg.sender,
            )
            return

        block = runtime.node.blockchain.blocks.get(vote.block_hash)

        if block is None or block.view != vote.view:
            return

        if runtime.proposed.get(vote.view) != vote.block_hash:
            return

        vote_key = (vote.view, vote.block_hash)
        collected = runtime.votes.setdefault(vote_key, {})

        # Los duplicados no aumentan el cuórum.
        if vote.validator_id in collected:
            self._record(
                "DUPLICATE_VOTE",
                node=recipient,
                sender=vote.validator_id,
            )
            return

        collected[vote.validator_id] = vote

        self._record(
            "VOTE_ACCEPTED",
            node=recipient,
            view=vote.view,
            count=len(collected),
        )

        if len(collected) < self.quorum:
            return

        if vote_key in runtime.formed_qcs:
            return

        qc = QuorumCertificate(
            view=vote.view,
            block_hash=vote.block_hash,
            votes=tuple(collected.values()),
        )

        if not qc.verify(self.public_keys, self.quorum):
            return

        runtime.formed_qcs.add(vote_key)

        self._record(
            "QC_FORMED",
            node=recipient,
            view=qc.view,
            block=qc.block_hash,
        )

        # Incluye al líder, que también debe procesar el QC.
        self.network.broadcast(
            recipient,
            "QC",
            qc,
            include_sender=True,
        )

    def _on_qc(
        self,
        recipient: str,
        msg: Envelope,
    ) -> None:
        node = self.nodes[recipient].node
        qc = msg.payload

        if not isinstance(qc, QuorumCertificate):
            return

        if not node.receive_qc(qc):
            return

        self._record(
            "QC_RECEIVED",
            node=recipient,
            view=qc.view,
        )

        self._update_chain(node, qc.block_hash)

    def _update_chain(
        self,
        node: HotStuffNode,
        block_hash: str,
    ) -> None:
        """Regla educativa de tres cadenas consecutivas."""
        chain = node.blockchain
        b3 = chain.blocks.get(block_hash)

        if b3 is None or b3.height < 3:
            return

        b2 = chain.blocks.get(b3.parent_hash)
        if b2 is None:
            return

        b1 = chain.blocks.get(b2.parent_hash)
        if b1 is None:
            return

        # Cada bloque debe tener un QC verificado.
        if not all(b.block_hash in node.certificates for b in (b1, b2, b3)):
            return

        # La regla de tres cadenas exige vistas consecutivas.
        if not (b2.view == b1.view + 1 and b3.view == b2.view + 1):
            return

        # El padre certificado determina el nuevo bloqueo.
        node.validator.update_lock(
            b2.block_hash,
            b2.view,
        )
        node.locked_qc = node.certificates[b2.block_hash]

        if chain.is_committed(b1.block_hash):
            return

        try:
            committed = chain.commit(b1.block_hash)
        except Exception as exc:
            self._record(
                "COMMIT_REJECTED",
                node=node.node_id,
                reason=str(exc),
            )
            return

        self._record(
            "COMMITTED",
            node=node.node_id,
            view=b3.view,
            blocks=committed,
            height=chain.committed_height,
        )

    def _on_timeout(self, recipient: str, msg: Envelope) -> None:
        notice = msg.payload
        if not isinstance(notice, SignedTimeout):
            return
        if msg.sender != notice.validator_id or not notice.verify(self.public_keys):
            self._record("INVALID_TIMEOUT", node=recipient, sender=msg.sender)
            return
        if recipient != self.leader_id(notice.view + 1):
            return
        runtime = self.nodes[recipient]
        if notice.view in runtime.formed_tcs:
            return
        collected = runtime.timeouts.setdefault(notice.view, {})
        collected[notice.validator_id] = notice
        if len(collected) < self.quorum:
            return
        tc = TimeoutCertificate(notice.view, tuple(collected.values()))
        if not tc.verify(self.public_keys, self.quorum):
            return
        runtime.formed_tcs.add(notice.view)
        self._record(
            "TC_FORMED", node=recipient, view=notice.view, signers=sorted(collected)
        )
        self.network.broadcast(recipient, "TC", tc, include_sender=True)

    def _on_tc(self, recipient: str, msg: Envelope) -> None:
        tc = msg.payload
        if not isinstance(tc, TimeoutCertificate):
            return
        if msg.sender != self.leader_id(tc.view + 1):
            return
        if not tc.verify(self.public_keys, self.quorum):
            self._record("INVALID_TC", node=recipient, view=tc.view)
            return
        node = self.nodes[recipient].node
        if tc.view + 1 <= node.view:
            return
        node.view = tc.view + 1
        self._record("VIEW_CHANGED", node=recipient, view=node.view, reason="TC")
        self._send_new_view(recipient, node.view)

    def _send_new_view(self, sender: str, view: int) -> None:
        """Send authenticated highQC to the designated leader of the view."""
        node = self.nodes[sender].node
        message = NewView.create(
            validator_id=sender,
            private_key=node.validator.private_key,
            view=view,
            high_qc=node.high_qc,
        )
        self._record("NEW_VIEW_SENT", node=sender, view=view)
        self.network.send(sender, self.leader_id(view), "NEW_VIEW", message)

    def _on_new_view(self, recipient: str, msg: Envelope) -> None:
        message = msg.payload
        if not isinstance(message, NewView):
            return
        if recipient != self.leader_id(message.view):
            return
        if msg.sender != message.validator_id:
            self._record("NEW_VIEW_REJECTED", node=recipient, reason="sender_mismatch")
            return
        runtime = self.nodes[recipient]
        collector = runtime.new_views.setdefault(
            message.view,
            NewViewCollector(message.view, self.public_keys, self.quorum),
        )
        if not collector.add(message):
            self._record(
                "NEW_VIEW_REJECTED", node=recipient, reason="invalid_or_duplicate"
            )
            return
        self._record(
            "NEW_VIEW_ACCEPTED",
            node=recipient,
            view=message.view,
            count=len(collector.messages),
        )
        if collector.ready:
            selected = collector.highest_qc()
            self._record(
                "NEW_VIEW_QUORUM",
                node=recipient,
                view=message.view,
                high_qc_view=selected.view if selected else None,
                high_qc_hash=selected.block_hash if selected else self.genesis_hash,
            )

    def trigger_timeouts(self, view: int) -> None:
        """Educational timeout trigger; network transports signed notices."""
        next_leader = self.leader_id(view + 1)
        for node_id, runtime in self.nodes.items():
            if node_id in self.network.offline or runtime.node.view != view:
                continue
            notice = SignedTimeout.create(
                node_id, runtime.node.validator.private_key, view
            )
            self._record("TIMEOUT_SENT", node=node_id, view=view)
            self.network.send(node_id, next_leader, "TIMEOUT", notice)
        self.network.run()

    def run_round(self) -> RoundResult:
        current_view = self.view
        leader_id = self.leader_id(current_view)
        leader = self.nodes[leader_id].node

        block_hash = None

        if leader_id not in self.network.offline and leader.view == current_view:
            collector = self.nodes[leader_id].new_views.get(current_view)
            # In recovery views, wait for authenticated NEW_VIEW quorum.
            # If the parent is missing, stop rather than propose an unsafe block.
            if collector is not None and not collector.ready:
                self._record("WAIT_NEW_VIEW_QUORUM", node=leader_id, view=current_view)
                return RoundResult(
                    current_view,
                    leader_id,
                    None,
                    0,
                    False,
                    {nid: rt.node.committed_height for nid, rt in self.nodes.items()},
                )
            if collector is not None and collector.ready:
                selected = collector.highest_qc()
                if selected is not None and (
                    leader.high_qc is None or selected.view > leader.high_qc.view
                ):
                    if selected.block_hash not in leader.blockchain.blocks:
                        self._record(
                            "SYNC_REQUIRED",
                            node=leader_id,
                            view=current_view,
                            block=selected.block_hash,
                        )
                        return RoundResult(
                            current_view,
                            leader_id,
                            None,
                            0,
                            False,
                            {
                                nid: rt.node.committed_height
                                for nid, rt in self.nodes.items()
                            },
                        )
                    leader.receive_qc(selected)
            parent_hash = (
                leader.high_qc.block_hash
                if leader.high_qc is not None
                else self.genesis_hash
            )

            # Si el líder desconoce el bloque padre,
            # no puede construir una propuesta válida.
            if parent_hash in leader.blockchain.blocks:
                block = leader.blockchain.create_block(
                    parent_hash=parent_hash,
                    view=current_view,
                    proposer_id=leader_id,
                    transactions=[],
                )

                block_hash = block.block_hash

                self.nodes[leader_id].proposed[current_view] = block_hash

                self._record(
                    "PROPOSED",
                    node=leader_id,
                    view=current_view,
                    block=block_hash,
                )

                self.network.broadcast(
                    leader_id,
                    "PROPOSE",
                    Proposal(
                        block=block,
                        justify=leader.high_qc,
                    ),
                    include_sender=True,
                )

        # Procesa la entrega de propuestas, votos y QC.
        self.network.run()

        votes = 0
        qc_formed = False

        if block_hash is not None:
            key = (current_view, block_hash)
            votes = len(self.nodes[leader_id].votes.get(key, {}))
            qc_formed = any(
                event["event"] == "QC_FORMED" and event.get("view") == current_view
                for event in self.events
            )

        if qc_formed:
            # A successful round advances only online nodes that received
            # the certificate; disconnected nodes retain their local view.
            for node_id, runtime in self.nodes.items():
                if node_id not in self.network.offline and (
                    block_hash in runtime.node.certificates
                ):
                    runtime.node.view = max(runtime.node.view, current_view + 1)
                    self._send_new_view(node_id, runtime.node.view)
            self.network.run()
            self.view += 1
        else:
            # The next leader gathers signed timeouts and broadcasts a TC.
            self.trigger_timeouts(current_view)
            if self.nodes[self.leader_id(current_view + 1)].node.view > current_view:
                self.view += 1

        return RoundResult(
            view=current_view,
            leader=leader_id,
            block_hash=block_hash,
            votes=votes,
            qc_formed=qc_formed,
            committed_heights={
                nid: runtime.node.committed_height
                for nid, runtime in self.nodes.items()
            },
        )
