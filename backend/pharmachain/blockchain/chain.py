from pharmachain.blockchain.block import Block
from pharmachain.domain.state import LedgerState, ValidationError


class BlockchainError(Exception):
    pass


class Blockchain:
    def __init__(self, initial_state: LedgerState):
        self.genesis = Block.genesis()
        genesis_hash = self.genesis.block_hash

        self.blocks: dict[str, Block] = {
            genesis_hash: self.genesis,
        }

        self.states: dict[str, LedgerState] = {
            genesis_hash: initial_state.clone(),
        }

        self.committed: list[str] = [genesis_hash]
        self.committed_tip = genesis_hash

    def get_block(self, block_hash: str) -> Block:
        try:
            return self.blocks[block_hash]
        except KeyError as exc:
            raise BlockchainError("Unknown block") from exc

    def get_state(self, block_hash: str) -> LedgerState:
        try:
            return self.states[block_hash].clone()
        except KeyError as exc:
            raise BlockchainError("Unknown state") from exc

    def create_block(
        self,
        parent_hash: str,
        view: int,
        proposer_id: str,
        transactions: list,
    ) -> Block:
        parent = self.get_block(parent_hash)

        if view <= parent.view:
            raise BlockchainError("View must increase")

        return Block(
            parent_hash=parent_hash,
            height=parent.height + 1,
            view=view,
            proposer_id=proposer_id,
            transactions=tuple(transactions),
        )

    def add_block(self, block: Block) -> str:
        block_hash = block.block_hash

        if block_hash in self.blocks:
            raise BlockchainError("Duplicate block")

        parent = self.get_block(block.parent_hash)

        if block.height != parent.height + 1:
            raise BlockchainError("Invalid block height")

        if block.view <= parent.view:
            raise BlockchainError("Invalid block view")

        if not block.proposer_id:
            raise BlockchainError("Missing proposer")

        state = self.get_state(block.parent_hash)

        try:
            for tx in block.transactions:
                state = state.apply(tx)
        except (ValidationError, ValueError) as exc:
            raise BlockchainError(f"Invalid block transaction: {exc}") from exc

        self.blocks[block_hash] = block
        self.states[block_hash] = state

        return block_hash

    def _path_from_committed_tip(
        self,
        target_hash: str,
    ) -> list[str]:
        if target_hash not in self.blocks:
            raise BlockchainError("Unknown target block")

        path = []
        current_hash = target_hash

        while current_hash != self.committed_tip:
            block = self.blocks[current_hash]

            if block.height <= self.blocks[self.committed_tip].height:
                raise BlockchainError("Target does not extend committed chain")

            path.append(current_hash)
            current_hash = block.parent_hash

            if current_hash not in self.blocks:
                raise BlockchainError("Broken ancestry")

        return list(reversed(path))

    def commit(self, block_hash: str) -> list[str]:
        """
        Commit a block and its uncommitted ancestors.

        IMPORTANT:
        Only the HotStuff consensus engine must call this
        method after verifying the commit rule.
        """
        path = self._path_from_committed_tip(block_hash)

        self.committed.extend(path)
        self.committed_tip = block_hash

        return path

    def is_committed(self, block_hash: str) -> bool:
        return block_hash in self.committed

    @property
    def committed_state(self) -> LedgerState:
        return self.get_state(self.committed_tip)

    @property
    def committed_height(self) -> int:
        return self.blocks[self.committed_tip].height
