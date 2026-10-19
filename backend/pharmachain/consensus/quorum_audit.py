from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class QuorumAudit:
    total_validators: int
    quorum_required: int
    accepted_voters: tuple[str, ...]
    rejected_voters: tuple[str, ...]
    quorum_reached: bool

    def to_dict(self) -> dict:
        return asdict(self)


def inspect_quorum(
    accepted_voters: list[str],
    rejected_voters: list[str],
    total_validators: int = 4,
) -> QuorumAudit:
    if total_validators < 1:
        raise ValueError("Invalid validator count")

    quorum = (2 * total_validators) // 3 + 1

    accepted = tuple(sorted(set(accepted_voters)))
    rejected = tuple(sorted(set(rejected_voters) - set(accepted)))

    return QuorumAudit(
        total_validators=total_validators,
        quorum_required=quorum,
        accepted_voters=accepted,
        rejected_voters=rejected,
        quorum_reached=len(accepted) >= quorum,
    )
