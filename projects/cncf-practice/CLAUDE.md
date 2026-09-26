# cncf-practice

@.claude/RULES.md

CNCF certification (CKAD first, CKA etc. later) hands-on practice:
a local kind cluster on WSL2 + Docker Desktop, and killer.sh-style mock
exams that the agent writes and grades
(https://github.com/DeveloperRyou/cncf-practice).

## Commands

- `./scripts/install.sh` -- kubectl + kind into `~/.local/bin`, no sudo.
- `./scripts/up.sh` / `./scripts/down.sh` -- create/delete the `cncf`
  kind cluster (context `kind-cncf`). `up.sh` waits for the node and the
  default ServiceAccount, so pods can be created right after it returns.
- The host must be cgroup v2-only (`.wslconfig`
  `kernelCommandLine = cgroup_no_v1=all`); kubelet >= 1.35 won't start on
  cgroup v1. Don't reintroduce a `failCgroupV1: false` patch -- fix the
  host instead. `README.md` records the current tool versions; update it
  when they change.

## Mock exams

`docs/mock-exam.md` is the spec -- read it before writing or grading a
round, every time. The user's stated requirements, verbatim in spirit:

- The agent writes the exam, the user solves it and submits, the agent
  grades it.
- killer.sh format (hands-on in a real cluster), difficulty medium-hard,
  5 questions per round.
- One directory per certification (`ckad/`), one directory per round
  inside it (`ckad/round-01/`, ...), so each round feels like a mock exam.

Rules that are easy to get wrong:

- Never write solutions or explanations into the repo when writing a
  round -- they go into `result.md` only after grading. Don't reveal
  answers in chat either unless the user asks.
- Every question must be solvable on the local single-node kind cluster
  and precise enough (names, labels, ports, paths) to grade mechanically.
- Before writing a round, run it end to end yourself on a scratch
  cluster (`CLUSTER_NAME=scratch`): `setup.sh`, a reference solution
  kept outside the repo, then `grade.sh` must score 100; and `grade.sh`
  against an untouched `setup.sh` state must score ~0. Delete the
  scratch cluster afterwards.
- After grading, update `ckad/README.md` (score table + topic coverage).
