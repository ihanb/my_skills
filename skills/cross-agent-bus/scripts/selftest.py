#!/usr/bin/env python3
"""Reproducible end-to-end self-test for the cross-agent bus CLI.

Runs against isolated temporary bus roots; nothing is written to the user's
real ~/.agent-bus. Usage: python scripts/selftest.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLI = str(Path(__file__).with_name("agent_bus.py"))


def session():
    root = os.path.join(tempfile.mkdtemp(), "bus")
    env = dict(os.environ, AGENT_BUS_ROOT=root)

    def run(*args, expect_fail=False):
        proc = subprocess.run([sys.executable, CLI, *args], env=env, capture_output=True, text=True)
        if expect_fail:
            return proc.returncode != 0
        if proc.returncode != 0:
            raise AssertionError(f"{args} -> {proc.stderr.strip()}")
        return json.loads(proc.stdout)

    run.root = Path(root)
    return run


def past(seconds: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    checks: list[str] = []

    def ck(name: str, cond: bool) -> None:
        if not cond:
            raise AssertionError(name)
        checks.append(name)

    # ---- baseline protocol: registration, delivery, atomic claim, reply ----
    r = session()
    d = r("doctor")
    ck("baseline: doctor reports writable root", d["writable"] and d["bus_version"] == 1)
    a = r("register", "--id", "workbuddy@pc", "--tool", "workbuddy", "--caps", "research,docs,cpp")
    ck("baseline: first registration sees no peers", a["peers"] == [])
    r("register", "--id", "trae@pc", "--tool", "trae", "--caps", "frontend,react")
    c = r("register", "--id", "qoder@pc", "--tool", "qoder", "--caps", "java,spring")
    ck("baseline: discovery is incremental", len(c["peers"]) == 2)
    ck("baseline: discover lists 3", r("discover")["count"] == 3)
    ck("baseline: tool filter", r("discover", "--tool", "trae")["count"] == 1)
    s1 = r("send", "--from", "workbuddy@pc", "--to", "trae@pc", "--type", "task",
           "--subject", "login", "--body", '{"spec":"login form"}')
    tid = s1["ids"][0]
    ck("baseline: unicast delivered", s1["sent"] == 1)
    s2 = r("send", "--from", "workbuddy@pc", "--to", "*", "--type", "hello", "--subject", "hi", "--body", "{}")
    ck("baseline: broadcast excludes sender", s2["sent"] == 2 and "workbuddy@pc" not in s2["recipients"])
    ck("baseline: backlog", r("poll", "--id", "trae@pc")["count"] == 2)
    cl = r("claim", "--id", "trae@pc", "--msg-id", tid)
    ck("baseline: claim returns full message", cl["claimed"] == tid and cl["message"]["trust"] == "untrusted")
    ck("baseline: body preserved", cl["message"]["body"]["spec"] == "login form")
    ck("baseline: no double claim", r("claim", "--id", "trae@pc", "--msg-id", tid)["claimed"] is None)
    ack = r("ack", "--id", "trae@pc", "--msg-id", tid, "--reply-json", '{"status":"done"}')
    ck("baseline: ack + auto reply", ack["acked"] == tid and bool(ack["reply_id"]))
    pol = r("poll", "--id", "workbuddy@pc")
    ck("baseline: reply routed back", pol["count"] == 1 and pol["messages"][0]["type"] == "reply")
    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda _: r("claim", "--id", "qoder@pc"), range(6)))
    ck("baseline: concurrent claim has one winner", len([x for x in results if x["claimed"]]) == 1)
    ck("baseline: heartbeat", r("heartbeat", "--id", "qoder@pc")["id"] == "qoder@pc")
    ck("baseline: purge dry-run", r("purge", "--dry-run")["dry_run"] is True)
    r("purge")
    ck("baseline: purge", True)
    ck("baseline: doctor sees 3 peers", r("doctor")["online_peers"] == 3)
    ck("baseline: path traversal rejected", r("register", "--id", "../evil", expect_fail=True))
    ck("baseline: invalid body rejected",
       r("send", "--from", "workbuddy@pc", "--to", "trae@pc", "--body", "not-json", expect_fail=True))
    ck("baseline: unknown type rejected",
       r("send", "--from", "workbuddy@pc", "--to", "trae@pc", "--type", "exec", expect_fail=True))

    # ---- identity: sender verification and snapshots ----
    r = session()
    for agent, tool in (("a@pc", "workbuddy"), ("b@pc", "trae"), ("c@pc", "qoder")):
        r("register", "--id", agent, "--tool", tool, "--workspace", "E:/repo")
    ck("identity: unregistered sender rejected",
       r("send", "--from", "ghost@pc", "--to", "sink@pc", "--body", "{}", expect_fail=True))
    g = r("send", "--from", "ghost@pc", "--to", "sink@pc", "--body", "{}", "--no-verify-sender")
    ck("identity: explicit bypass allowed", g["sent"] == 1 and g["sender_verified"] is False)
    gid = g["ids"][0]
    gm = r("claim", "--id", "sink@pc", "--msg-id", gid)["message"]
    ck("identity: bypass message marked unverified", gm["sender"]["verified"] is False)
    r("ack", "--id", "sink@pc", "--msg-id", gid)
    v = r("send", "--from", "a@pc", "--to", "sink@pc", "--body", '{"intent":"x"}')
    ck("identity: registered sender verified", v["sender_verified"] is True)
    snap = r("claim", "--id", "sink@pc", "--msg-id", v["ids"][0])["message"]["sender"]
    ck("identity: snapshot carries tool/workspace",
       snap["tool"] == "workbuddy" and snap["verified"] is True and snap["workspace"].endswith("repo"))
    r("ack", "--id", "sink@pc", "--msg-id", v["ids"][0])

    # ---- delivery: broadcast is now explicit in the message ----
    bc = r("send", "--from", "a@pc", "--to", "*", "--type", "hello", "--subject", "hi", "--body", "{}")
    ck("delivery: broadcast mode + shared id",
       bc["mode"] == "broadcast" and len(bc["broadcast_id"]) == 12 and bc["sent"] == 2)
    m1 = r("claim", "--id", "b@pc", "--msg-id", bc["ids"][0])["message"]
    ck("delivery: recipients visible to receiver",
       m1["delivery"]["mode"] == "broadcast"
       and m1["delivery"]["broadcast_id"] == bc["broadcast_id"]
       and set(m1["delivery"]["recipients"]) == {"b@pc", "c@pc"})
    r("ack", "--id", "b@pc", "--msg-id", bc["ids"][0])
    m2 = r("claim", "--id", "c@pc", "--msg-id", bc["ids"][1])["message"]
    ck("delivery: same broadcast id across copies", m2["delivery"]["broadcast_id"] == bc["broadcast_id"])
    r("ack", "--id", "c@pc", "--msg-id", bc["ids"][1])
    dr = r("send", "--from", "a@pc", "--to", "sink@pc", "--body", "{}")
    dm = r("claim", "--id", "sink@pc", "--msg-id", dr["ids"][0])["message"]
    ck("delivery: direct mode has no broadcast id",
       dm["delivery"]["mode"] == "direct" and dm["delivery"]["broadcast_id"] == "")
    r("ack", "--id", "sink@pc", "--msg-id", dr["ids"][0])

    # ---- business timing: deadline, not_before, expiry notification ----
    dl = r("send", "--from", "a@pc", "--to", "sink@pc", "--body", "{}", "--deadline-sec", "-1")
    ck("timing: deadline recorded", bool(dl["deadline"]))
    cl = r("claim", "--id", "sink@pc", "--msg-id", dl["ids"][0])
    ck("timing: expired task refused", cl["claimed"] is None and cl["expired"] == 1)
    pol = r("poll", "--id", "a@pc")
    ck("timing: expiry notification sent",
       pol["count"] >= 1 and any(m["type"] == "reply" for m in pol["messages"]))
    rep = r("claim", "--id", "a@pc", "--msg-id", pol["messages"][0]["id"])["message"]
    ck("timing: reply marks status expired", rep["body"]["status"] == "expired")
    r("ack", "--id", "a@pc", "--msg-id", pol["messages"][0]["id"])
    nb = r("send", "--from", "a@pc", "--to", "sink@pc", "--body", "{}", "--not-before-sec", "3600")
    nid = nb["ids"][0]
    cl = r("claim", "--id", "sink@pc", "--msg-id", nid)
    ck("timing: future message deferred", cl["claimed"] is None and cl["deferred"] == 1)
    ck("timing: deferred message stays queued",
       any(m["id"] == nid for m in r("poll", "--id", "sink@pc")["messages"]))

    # ---- revocation: revoke + supersedes ----
    r("send", "--from", "a@pc", "--to", "sink@pc", "--type", "revoke",
      "--body", json.dumps({"target": nid}))
    pol = r("poll", "--id", "sink@pc")
    ck("revocation: revoke retires target",
       pol["revoked_removed"] >= 1 and not any(m["id"] == nid for m in pol["messages"]))
    ck("revocation: revoke requires target",
       r("send", "--from", "a@pc", "--to", "sink@pc", "--type", "revoke", "--body", "{}", expect_fail=True))
    old = r("send", "--from", "a@pc", "--to", "sink@pc", "--subject", "old", "--body", "{}")["ids"][0]
    r("send", "--from", "a@pc", "--to", "sink@pc", "--subject", "new", "--body", "{}", "--supersedes", old)
    pol = r("poll", "--id", "sink@pc")
    ck("revocation: supersedes retires old",
       pol["revoked_removed"] >= 1 and not any(m["id"] == old for m in pol["messages"]))
    ck("revocation: malformed supersedes rejected",
       r("send", "--from", "a@pc", "--to", "sink@pc", "--body", "{}", "--supersedes", "../bad", expect_fail=True))

    # ---- lazy expiry: poll sweeps by default, --no-sweep is read-only ----
    r("send", "--from", "a@pc", "--to", "sink@pc", "--body", "{}", "--ttl", "-1")
    p1 = r("poll", "--id", "sink@pc", "--no-sweep")
    ck("expiry: no-sweep reports expired", p1["expired_removed"] >= 1 and p1["sweep"] is False)
    p2 = r("poll", "--id", "sink@pc", "--no-sweep")
    ck("expiry: no-sweep keeps the file", p2["expired_removed"] >= 1)
    p3 = r("poll", "--id", "sink@pc")
    ck("expiry: default sweep deletes expired", p3["expired_removed"] >= 1)
    ck("expiry: sweep is idempotent", r("poll", "--id", "sink@pc")["expired_removed"] == 0)
    ck("expiry: doctor still healthy", r("doctor")["online_peers"] == 3)

    # ---- hardening: explicit leases instead of inherited inode mtime ----
    h = session()
    h("register", "--id", "a@pc", "--tool", "workbuddy")
    h("register", "--id", "b@pc", "--tool", "trae")
    aged = h("send", "--from", "a@pc", "--to", "b@pc", "--body", "{}")["ids"][0]
    src = h.root / "inbox" / "b@pc" / f"{aged}.json"
    stale = time.time() - 1000
    os.utime(src, (stale, stale))
    ck("lease: an aged queued message is still claimable",
       h("claim", "--id", "b@pc", "--msg-id", aged)["claimed"] == aged)
    claimed = h.root / "inbox" / "b@pc" / "claimed" / f"{aged}.json"
    lease = claimed.with_suffix(".lease")
    ck("lease: claim writes an explicit lease record", lease.exists())
    ck("lease: claimed inode mtime is refreshed", time.time() - claimed.stat().st_mtime < 30)
    ck("lease: a fresh claim is NOT requeued by purge",
       h("purge")["requeued"] == 0 and not src.exists())
    rec = json.loads(lease.read_text(encoding="utf-8"))
    rec["claimed_at"] = past(1000)
    lease.write_text(json.dumps(rec), encoding="utf-8")
    ck("lease: an expired lease does requeue", h("purge")["requeued"] == 1 and src.exists())
    ck("lease: requeue drops the stale lease", not lease.exists())
    h("claim", "--id", "b@pc", "--msg-id", aged)
    h("ack", "--id", "b@pc", "--msg-id", aged)
    ck("lease: ack removes the lease record", not lease.exists())

    # ---- hardening: tombstones make revocation durable ----
    target = h("send", "--from", "a@pc", "--to", "b@pc", "--subject", "old", "--body", "{}")["ids"][0]
    rv = h("send", "--from", "a@pc", "--to", "b@pc", "--type", "revoke",
           "--body", json.dumps({"target": target}))["ids"][0]
    tomb = h.root / "retired" / "b@pc" / f"{target}.json"
    ck("tombstone: revoke writes a durable record at delivery", tomb.exists())
    h("claim", "--id", "b@pc", "--msg-id", rv)
    h("ack", "--id", "b@pc", "--msg-id", rv)
    pol = h("poll", "--id", "b@pc")
    ck("tombstone: revocation survives the revoke being consumed",
       not any(m["id"] == target for m in pol["messages"]))
    old2 = h("send", "--from", "a@pc", "--to", "b@pc", "--subject", "old2", "--body", "{}")["ids"][0]
    h("send", "--from", "a@pc", "--to", "b@pc", "--subject", "new", "--body", "{}",
      "--supersedes", old2)
    ck("tombstone: supersedes also persists", (h.root / "retired" / "b@pc" / f"{old2}.json").exists())
    ck("tombstone: doctor reports them", h("doctor")["retired_total"] >= 2)
    rec = json.loads(tomb.read_text(encoding="utf-8"))
    rec["at"] = past(8 * 86400)
    tomb.write_text(json.dumps(rec), encoding="utf-8")
    ck("tombstone: purge plans stale ones", h("purge", "--dry-run")["retired_expired"] >= 1)
    h("purge")
    ck("tombstone: purge removes stale ones", not tomb.exists())

    # ---- hardening: dry-run plans real work without touching files ----
    exp = h("send", "--from", "a@pc", "--to", "b@pc", "--body", "{}", "--ttl", "-1")["ids"][0]
    exp_file = h.root / "inbox" / "b@pc" / f"{exp}.json"
    dry = h("purge", "--dry-run")
    ck("dry-run: reports the planned removals", dry["dry_run"] is True and dry["expired_messages"] >= 1)
    ck("dry-run: leaves every file in place", exp_file.exists())
    real = h("purge")
    ck("dry-run: commit matches the plan", real["expired_messages"] == dry["expired_messages"] and not exp_file.exists())

    # ---- hardening: silent misdelivery is now visible ----
    bad = h("send", "--from", "a@pc", "--to", "ghost@typo", "--body", "{}")
    ck("delivery: unknown recipient is flagged",
       bad["recipient_registered"] is False and any("no registration record" in w for w in bad["warnings"]))
    solo = session()
    solo("register", "--id", "solo@pc")
    empty = solo("send", "--from", "solo@pc", "--to", "*", "--type", "hello", "--body", "{}")
    ck("delivery: empty broadcast is flagged",
       empty["sent"] == 0 and any("no online peers" in w for w in empty["warnings"]))

    # ---- hardening: unique threads + read-only inspect ----
    t = session()
    t("register", "--id", "a@pc")
    t("register", "--id", "b@pc")
    x = t("send", "--from", "a@pc", "--to", "b@pc", "--body", '{"intent":"one"}')
    y = t("send", "--from", "a@pc", "--to", "b@pc", "--body", '{"intent":"two"}')
    ck("thread: two sends in the same second get distinct threads", x["thread"] != y["thread"])
    one = t("inspect", "--msg-id", x["ids"][0])
    ck("inspect: by-id returns the full message",
       one["found"] >= 1 and one["copies"][0]["message"]["body"]["intent"] == "one")
    before = t("poll", "--id", "b@pc", "--no-sweep")["total"]
    t("inspect", "--msg-id", x["ids"][0])
    ck("inspect: never changes message state",
       t("poll", "--id", "b@pc", "--no-sweep")["total"] == before)
    th = t("inspect", "--thread", x["thread"])
    ck("inspect: thread view isolates one collaboration round",
       th["count"] == 1 and th["messages"][0]["id"] == x["ids"][0])
    cl = t("claim", "--id", "b@pc", "--msg-id", x["ids"][0])
    ck("inspect: claim still works after inspection", cl["claimed"] == x["ids"][0])
    t("ack", "--id", "b@pc", "--msg-id", x["ids"][0], "--reply-json", '{"status":"done"}')
    th2 = t("inspect", "--thread", x["thread"])
    ck("inspect: thread view includes the reply",
       th2["count"] == 2 and any(m["type"] == "reply" for m in th2["messages"]))
    ck("inspect: selectors are mutually exclusive",
       t("inspect", "--msg-id", x["ids"][0], "--thread", x["thread"], expect_fail=True))
    ck("inspect: a selector is required", t("inspect", expect_fail=True))
    ck("inspect: path traversal in --msg-id rejected",
       t("inspect", "--msg-id", "../evil", expect_fail=True))
    ck("discover: invalid --exclude rejected",
       t("discover", "--exclude", "../evil", expect_fail=True))

    print(f"PASS: {len(checks)} checks")
    for name in checks:
        print("  -", name)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
