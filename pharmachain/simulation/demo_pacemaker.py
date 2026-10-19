from pharmachain.consensus.pacemaker import Pacemaker


def main():
    nodes = [f"validator-{i}" for i in range(4)]
    pacemaker = Pacemaker(nodes, timeout=2.0)

    online = set(nodes)
    online.remove("validator-0")

    print("=== HOTSTUFF PACEMAKER ===")
    print("Validators:", len(nodes))
    print("Quorum:", pacemaker.quorum)
    print("Initial leader:", pacemaker.leader(1))
    print("Offline:", "validator-0")

    print("\nTIME = 1.0")
    notices = pacemaker.tick(1.0, online)
    print("Timeouts:", len(notices))

    print("\nTIME = 2.0")
    notices = pacemaker.tick(2.0, online)

    tc = None

    for notice in notices:
        print(
            "TIMEOUT",
            notice.validator_id,
            "view",
            notice.view,
        )

        result = pacemaker.receive_timeout(
            notice,
            2.0,
        )

        if result is not None:
            tc = result

    if tc is None:
        print("No timeout certificate")
        return

    print("\nTIMEOUT CERTIFICATE")
    print("View:", tc.view)
    print("Signers:", sorted(tc.signers))

    print("\nADVANCING HONEST NODES")

    for node in sorted(online):
        pacemaker.advance(node, tc, 2.0)

        print(
            node,
            "new view:",
            pacemaker.view[node],
        )

    print("\nNew leader:", pacemaker.leader(2))

    print("\nEVENT LOG")

    for event in pacemaker.events:
        print(event)


if __name__ == "__main__":
    main()
