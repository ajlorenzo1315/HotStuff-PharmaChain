from pharmachain.consensus.pacemaker import Pacemaker


def make():
    return Pacemaker(
        [f"validator-{i}" for i in range(4)],
        timeout=2,
    )


def test_leaders():
    p = make()

    assert [p.leader(v) for v in range(1, 6)] == [
        "validator-0",
        "validator-1",
        "validator-2",
        "validator-3",
        "validator-0",
    ]


def test_no_early_timeout():
    p = make()

    assert p.tick(1, set(p.validator_ids)) == []


def test_timeout_once():
    p = make()
    online = set(p.validator_ids)

    assert len(p.tick(2, online)) == 4
    assert p.tick(3, online) == []


def test_quorum():
    p = make()
    notices = p.tick(2, set(p.validator_ids))

    assert p.receive_timeout(notices[0], 2) is None
    assert p.receive_timeout(notices[1], 2) is None

    tc = p.receive_timeout(notices[2], 2)

    assert tc is not None
    assert len(tc.signers) == 3
    assert p.receive_timeout(notices[3], 2) is None


def test_advance():
    p = make()
    notices = p.tick(2, set(p.validator_ids))

    tc = None
    for notice in notices[:3]:
        tc = p.receive_timeout(notice, 2)

    assert p.advance("validator-0", tc, 2)
    assert p.view["validator-0"] == 2

    assert not p.advance("validator-0", tc, 2)
    assert p.deadline["validator-0"] == 4


def test_two_nodes_insufficient():
    p = make()

    notices = p.tick(
        2,
        {"validator-0", "validator-1"},
    )

    assert all(p.receive_timeout(notice, 2) is None for notice in notices)

    assert not p.certificates


def test_progress_resets_deadline():
    p = make()

    p.on_progress("validator-0", 1, 1)

    assert p.view["validator-0"] == 2
    assert p.tick(2, {"validator-0"}) == []
    assert len(p.tick(3, {"validator-0"})) == 1
