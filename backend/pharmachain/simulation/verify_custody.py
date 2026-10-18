#!/usr/bin/env python3
"""HTTP black-box custody checks for the distributed PharmaChain demo.
Run against an isolated local test server; this script resets its simulation.
"""

import argparse
import json
import sys
import urllib.error
import urllib.request


class API:
    def __init__(self, base):
        self.base = base.rstrip("/")

    def call(self, path, payload=None):
        req = urllib.request.Request(
            self.base + path,
            method="POST" if payload is not None else "GET",
            data=json.dumps(payload).encode() if payload is not None else None,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"{path}: HTTP {exc.code}: {exc.read().decode()[:400]}") from exc

    def reset(self):
        return self.call("/api/simulation/reset", {})

    def state(self):
        return self.call("/api/simulation")

    def round(self):
        return self.call("/api/simulation/round", {})

    def disconnect(self, node):
        return self.call("/api/simulation/disconnect", {"node_id": node})

    def reconnect(self, node):
        return self.call("/api/simulation/reconnect", {"node_id": node})


def custodians(s, batch):
    return {node: batches.get(batch) for node, batches in s.get("custody_by_node", {}).items()}


def events(s, event):
    return [e for e in s.get("events", []) if e.get("event") == event]


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print("PASS:", message)


def advance(api, batch, expected, limit=12):
    for i in range(limit):
        result = api.round()
        s = result.get("state") or api.state()
        c = custodians(s, batch)
        print(f"  ronda {i + 1}: vista={s.get('view')} custodia={c} pendiente={len(s.get('pending_transactions', []))}")
        if c and all(v == expected for v in c.values()):
            return s
    return api.state()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8010")
    args = parser.parse_args()
    api = API(args.url)
    batch = "LOT-CUSTODY-TEST"
    print("\n1. REGISTRO PENDIENTE")
    s = api.reset()
    check(s.get("pharmaceutical_transactions_enabled") is True, "API de transacciones distribuidas habilitada")
    s = api.call("/api/simulation/batches/register", {"batch_id": batch, "medicine_name": "Amoxicilina", "quantity": 100})
    check(all(v is None for v in custodians(s, batch).values()), "Registro pendiente NO modifica estado confirmado")
    check(any(tx["batch_id"] == batch for tx in s["pending_transactions"]), "Registro figura en mempool")
    s = advance(api, batch, "laboratory")
    check(all(v == "laboratory" for v in custodians(s, batch).values()), "Registro confirmado en todos los validadores")
    print("\n2. TRANSFERENCIA PENDIENTE Y CONFIRMADA")
    s = api.call("/api/simulation/batches/transfer", {"batch_id": batch, "sender_id": "laboratory", "receiver_id": "distributor"})
    check(all(v == "laboratory" for v in custodians(s, batch).values()), "Transferencia pendiente conserva custodio anterior")
    s = advance(api, batch, "distributor")
    check(all(v == "distributor" for v in custodians(s, batch).values()), "Transferencia confirmada cambia custodio en todos los validadores")
    print("\n3. ATAQUE: SIN CUORUM")
    api.reset()
    api.disconnect("validator-2")
    api.disconnect("validator-3")
    s = api.call("/api/simulation/batches/register", {"batch_id": batch, "medicine_name": "Amoxicilina", "quantity": 100})
    for _ in range(4):
        s = api.round().get("state") or api.state()
    check(all(v is None for v in custodians(s, batch).values()), "Con 2/4 validadores NO se crea custodia confirmada")
    check(any(tx["batch_id"] == batch for tx in s.get("pending_transactions", [])), "Transaccion bloqueada sigue pendiente")
    print("\n4. RECUPERACION (diagnostico de vivacidad)")
    api.reconnect("validator-2")
    api.reconnect("validator-3")
    s = advance(api, batch, "laboratory", limit=12)
    if all(v == "laboratory" for v in custodians(s, batch).values()):
        print("PASS: transaccion confirmada tras recuperar conectividad")
    else:
        print("PENDIENTE: la transaccion no se reproponio/confirma tras recuperar la red.")
        print("Esto revela una limitacion de vivacidad/repropuesta; NO debe mostrarse como transferencia completada.")
    print("\nEventos recientes:", [e.get("event") for e in s.get("events", [])[-12:]])
    print("\nPruebas finalizadas; consulta los PASS y el diagnostico de recuperacion.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, RuntimeError, urllib.error.URLError, KeyError) as exc:
        print("FAIL:", exc, file=sys.stderr)
        sys.exit(1)
