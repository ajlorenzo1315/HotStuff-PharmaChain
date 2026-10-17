"""Estado local de un validador HotStuff."""

from dataclasses import dataclass, field

from pharmachain.blockchain.block import Block
from pharmachain.blockchain.chain import Blockchain, BlockchainError
from pharmachain.consensus.messages import QuorumCertificate
from pharmachain.consensus.validator import Validator
from pharmachain.domain.state import LedgerState


@dataclass
class HotStuffNode:
    validator: Validator
    blockchain: Blockchain
    public_keys: dict[str, str]
    quorum: int
    view: int = 1
    high_qc: QuorumCertificate | None = None
    locked_qc: QuorumCertificate | None = None
    certificates: dict[str, QuorumCertificate] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        validator: Validator,
        initial_state: LedgerState,
        public_keys: dict[str, str],
        quorum: int,
    ) -> "HotStuffNode":
        return cls(
            validator=validator,
            blockchain=Blockchain(initial_state),
            public_keys=public_keys.copy(),
            quorum=quorum,
        )

    @property
    def node_id(self) -> str:
        return self.validator.validator_id

    @property
    def committed_height(self) -> int:
        return self.blockchain.committed_height

    def receive_block(self, block: Block) -> bool:
        if block.block_hash in self.blockchain.blocks:
            return True

        try:
            self.blockchain.add_block(block)
        except BlockchainError:
            return False

        return True

    def receive_qc(
        self,
        qc: QuorumCertificate,
    ) -> bool:
        if not qc.verify(self.public_keys, self.quorum):
            return False

        block = self.blockchain.blocks.get(qc.block_hash)

        if block is None or block.view != qc.view:
            return False

        self.certificates[qc.block_hash] = qc

        if self.high_qc is None or qc.view > self.high_qc.view:
            self.high_qc = qc

        return True

    def is_ancestor(
        self,
        ancestor_hash: str,
        descendant_hash: str,
    ) -> bool:
        current = descendant_hash

        while current in self.blockchain.blocks:
            if current == ancestor_hash:
                return True

            block = self.blockchain.blocks[current]

            if block.height == 0:
                break

            current = block.parent_hash

        return False

    def is_safe(
        self,
        parent_hash: str,
        justify_qc: QuorumCertificate | None,
    ) -> bool:
        if parent_hash not in self.blockchain.blocks:
            return False

        locked_hash = self.validator.locked_block_hash

        if locked_hash is None:
            return True

        if self.is_ancestor(locked_hash, parent_hash):
            return True

        if justify_qc is None:
            return False

        if justify_qc.block_hash != parent_hash:
            return False

        if not justify_qc.verify(self.public_keys, self.quorum):
            return False

        return justify_qc.view > self.validator.locked_view
