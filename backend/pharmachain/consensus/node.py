from dataclasses import dataclass, field

from pharmachain.blockchain.chain import Blockchain
from pharmachain.consensus.messages import QuorumCertificate
from pharmachain.consensus.validator import Validator
from pharmachain.domain.state import LedgerState


@dataclass
class HotStuffNode:
    validator: Validator
    blockchain: Blockchain
    view: int = 1
    high_qc: QuorumCertificate | None = None
    locked_qc: QuorumCertificate | None = None
    certificates: dict[str, QuorumCertificate] = field(default_factory=dict)

    @classmethod
    def create(
        cls,
        validator: Validator,
        initial_state: LedgerState,
    ) -> "HotStuffNode":
        return cls(
            validator=validator,
            blockchain=Blockchain(initial_state),
        )

    def receive_qc(
        self,
        qc: QuorumCertificate,
        public_keys: dict[str, str],
        quorum: int,
    ) -> bool:
        if not qc.verify(public_keys, quorum):
            return False

        # No aceptar certificados de bloques desconocidos.
        if qc.block_hash not in self.blockchain.blocks:
            return False

        self.certificates[qc.block_hash] = qc

        if self.high_qc is None or qc.view > self.high_qc.view:
            self.high_qc = qc

        return True
