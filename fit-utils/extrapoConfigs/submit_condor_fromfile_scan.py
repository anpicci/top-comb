#!/usr/bin/env python3
# submit_condor_fromfile_scan.py
#
# Generate & submit HTCondor jobs for a CSV-based fixed-point scan.
#
# Each Condor job:
#   - receives a chunk CSV + workspace + wrapper via file transfer
#   - sets up CMSSW from your AFS CMSSW area
#   - runs parallel_fromfile_scan.py with -j = request_cpus
#   - bundles results under bundle_chunk<id>/ and transfers that back
#
# Runner script is generated without "set -Eeuo pipefail" (Option C),
# with explicit checks, explicit exits, and a failure diagnostic artifact
# copied into bundle_chunk<ID>/ even on crash.
#
# NEW:
#   - always generates condor_fromfile_scan_failed.sub (queue from failed_chunks.list)
#   - writes RUN_CONFIG.json in run_dir for post-run tooling
#   - supports post-run modes:
#       --make_failed_list     -> create failed_chunks.list by scanning bundle_chunk*/ expected roots
#       --resubmit_failed      -> (optionally) submit the failed-only file
#       --collect_outputs      -> copy per-chunk roots into output/ and hadd them
#
import argparse
import getpass
import json
import os
import random
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass, asdict
from math import ceil
from pathlib import Path
from typing import Optional, Any


def read_non_empty_lines(path: Path) -> list[str]:
    return [l.rstrip("\n") for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def recreate_dir_from_scratch(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def resolve_path_maybe_relative(base_dir: Path, p: str) -> Path:
    if os.path.isabs(p):
        return Path(p).resolve()
    return (base_dir / p).resolve()


def extract_opt_value(args: list[str], keys: list[str], default=None):
    for i, a in enumerate(args):
        for k in keys:
            if a == k and i + 1 < len(args):
                return args[i + 1]
            if a.startswith(k + "="):
                return a.split("=", 1)[1]
    return default


def remove_opts(args: list[str], keys: list[str]) -> list[str]:
    out: list[str] = []
    i = 0
    while i < len(args):
        a = args[i]
        matched = False
        for k in keys:
            if a == k:
                matched = True
                i += 2
                break
            if a.startswith(k + "="):
                matched = True
                i += 1
                break
        if not matched:
            out.append(a)
            i += 1
    return out


def format_mass_g(mass_value) -> str:
    try:
        return f"{float(mass_value):g}"
    except Exception:
        return str(mass_value)


# --------------------------
# Debug subset selection
# --------------------------

def parse_points_idx(expr: str, nrows: int) -> list[int]:
    expr = expr.strip()
    if not expr:
        raise ValueError("empty --points_idx expression")

    idxs: set[int] = set()
    for tok in expr.split(","):
        tok = tok.strip()
        if not tok:
            continue
        m = re.fullmatch(r"(\d+)(?:-(\d+))?", tok)
        if not m:
            raise ValueError(f"invalid token in --points_idx: '{tok}'")
        a = int(m.group(1))
        b = int(m.group(2)) if m.group(2) else a
        if a < 1 or b < 1 or a > nrows or b > nrows:
            raise ValueError(f"--points_idx token out of range (1..{nrows}): '{tok}'")
        if b < a:
            a, b = b, a
        for k in range(a, b + 1):
            idxs.add(k - 1)
    return sorted(idxs)


def parse_points_slice(expr: str, nrows: int) -> list[int]:
    expr = expr.strip()
    m = re.fullmatch(r"(\d*)\s*:\s*(\d*)", expr)
    if not m:
        raise ValueError("invalid --points_slice format. Use 'start:end' (1-based, inclusive), e.g. ':50' or '10:20'")

    start_s, end_s = m.group(1), m.group(2)
    start = int(start_s) if start_s else 1
    end = int(end_s) if end_s else nrows

    if start < 1 or end < 1 or start > nrows or end > nrows:
        raise ValueError(f"--points_slice out of range (1..{nrows}): '{expr}'")

    if end < start:
        start, end = end, start

    return list(range(start - 1, end))


def select_rows(
    rows: list[str],
    points_first: Optional[int],
    points_last: Optional[int],
    points_slice: Optional[str],
    points_idx: Optional[str],
    points_sample: Optional[int],
    seed: Optional[int],
) -> tuple[list[str], str]:
    selectors = [
        points_first is not None,
        points_last is not None,
        points_slice is not None,
        points_idx is not None,
        points_sample is not None,
    ]
    if sum(selectors) > 1:
        raise RuntimeError("Use only ONE of: --points_first / --points_last / --points_slice / --points_idx / --points_sample")

    n = len(rows)
    if n == 0:
        return rows, "all (empty)"

    if points_first is not None:
        k = max(0, min(points_first, n))
        return rows[:k], f"first {k} points"
    if points_last is not None:
        k = max(0, min(points_last, n))
        return rows[n - k:], f"last {k} points"
    if points_slice is not None:
        idxs = parse_points_slice(points_slice, n)
        return [rows[i] for i in idxs], f"slice {points_slice} ({len(idxs)} points)"
    if points_idx is not None:
        idxs = parse_points_idx(points_idx, n)
        return [rows[i] for i in idxs], f"idx {points_idx} ({len(idxs)} points)"
    if points_sample is not None:
        k = max(0, min(points_sample, n))
        rng = random.Random(seed if seed is not None else 12345)
        idxs = list(range(n))
        rng.shuffle(idxs)
        idxs = sorted(idxs[:k])
        return [rows[i] for i in idxs], f"sample {k} points (seed={seed if seed is not None else 12345})"

    return rows, "all points"


def write_selected_csv(header: str, selected_rows: list[str], out_path: Path) -> Path:
    out_path.write_text(header + "\n" + "\n".join(selected_rows) + "\n", encoding="utf-8")
    return out_path.resolve()


# --------------------------
# Chunking
# --------------------------

def split_rows_into_chunks(
    header: str,
    rows: list[str],
    chunks: int,
    out_dir: Path,
    prefix: str,
) -> tuple[list[tuple[int, Path]], Path]:
    if len(rows) < 1:
        raise RuntimeError("csv must contain at least one data row after filtering")

    total = len(rows)
    chunks = min(chunks, total)

    out_dir.mkdir(parents=True, exist_ok=True)
    chunk_infos: list[tuple[int, Path]] = []

    for i in range(chunks):
        start = int(ceil(total * i / float(chunks)))
        end = int(ceil(total * (i + 1) / float(chunks)) - 1)
        if end < start:
            continue

        chunk_path = (out_dir / f"{prefix}.{i}.csv").resolve()
        with chunk_path.open("w", encoding="utf-8") as f:
            f.write(header + "\n")
            for k in range(start, end + 1):
                f.write(rows[k] + "\n")

        chunk_infos.append((i, chunk_path))

    chunk_list_path = (out_dir / "chunks.list").resolve()
    with chunk_list_path.open("w", encoding="utf-8") as lst:
        for chunk_id, chunk_csv in chunk_infos:
            lst.write(f"{chunk_id} {chunk_csv}\n")

    return chunk_infos, chunk_list_path


# --------------------------
# Run config persistence (for post-run actions)
# --------------------------

@dataclass
class RunConfig:
    run_dir: str
    cmssw_src: str
    base_name: str
    method: str
    mass_g: str
    threads_per_job: int
    request_memory: int
    job_flavour: str
    getenv: bool
    sanitize_env: bool
    keep_point_outputs: bool
    keep_workdirs: bool
    workspace_path: str
    wrapper_path: str
    selected_csv_path: str
    chunk_list_path: str

    def expected_root_name(self, chunk_id: int) -> str:
        return f"higgsCombine{self.base_name}.chunk{chunk_id}.{self.method}.mH{self.mass_g}.root"


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


# --------------------------
# Condor scripts
# --------------------------

def write_runner_script(
    runner_path: Path,
    cmssw_src: Path,
    wrapper_src_abs: Path,
    workspace_src_abs: Path,
    method: str,
    mass_g: str,
    base_name: str,
    cpus_per_job: int,
    common_args: list[str],
    sanitize_env: bool,
    keep_point_outputs: bool,
    keep_workdirs: bool,
):
    common_args_str = " ".join(shlex.quote(a) for a in common_args)

    wrapper_base = wrapper_src_abs.name
    workspace_base = workspace_src_abs.name

    content = f"""#!/usr/bin/env bash
# Option C runner: NO set -Eeuo pipefail.
# Explicit checks + explicit exits; on failure writes bundle_chunk<ID>/FAIL_DIAG.txt and copies logs if present.

chunk_id="$1"
chunk_csv_src="$2"
cpus="${{3:-{cpus_per_job}}}"

cmssw_src="{cmssw_src}"
wrapper_local="{wrapper_base}"
workspace_local="{workspace_base}"

base_name="{base_name}"
method="{method}"
mass="{mass_g}"

keep_point_outputs="{1 if keep_point_outputs else 0}"
keep_workdirs="{1 if keep_workdirs else 0}"

job_dir="$PWD"
bundle="bundle_chunk${{chunk_id}}"

die() {{
  echo "[runner] FATAL: $1"
  exit "${{2:-1}}"
}}

# Always ensure bundle exists, so transfer_output_files never fails due to missing dir
mkdir -p "$bundle" || true

write_fail_diag() {{
  rc="$1"
  if [ "$rc" -eq 0 ]; then
    return 0
  fi

  diag="$bundle/FAIL_DIAG.txt"
  {{
    echo "[runner] ERROR: job failed rc=$rc"
    echo "[runner] pwd=$(pwd)"
    echo "[runner] hostname=$(hostname)"
    echo "[runner] time=$(date -Is)"
    echo "[runner] chunk_id=$chunk_id"
    echo "[runner] chunk_csv_src=$chunk_csv_src"
    echo "[runner] wrapper_local=$wrapper_local"
    echo "[runner] workspace_local=$workspace_local"
    echo
    echo "[runner] ls -al:"
    ls -al || true
    echo
    echo "[runner] df -h:"
    df -h || true
    echo
    echo "[runner] logs dir listing (if any):"
    ls -al logs 2>/dev/null || true
    echo
    lastlog="$(ls -1t logs/POINT.*.log 2>/dev/null | head -n 1 || true)"
    if [ -n "$lastlog" ]; then
      echo "[runner] tail -n 200 $lastlog"
      tail -n 200 "$lastlog" || true
    fi
  }} > "$diag" 2>&1 || true

  # Copy logs into bundle if they exist (best-effort)
  if [ -d "logs" ]; then
    if [ ! -e "$bundle/logs" ]; then
      cp -a logs "$bundle/" 2>/dev/null || true
    fi
  fi
}}

trap 'write_fail_diag $?' EXIT

echo "[runner] starting"
echo "[runner] chunk_id=${{chunk_id}} cpus=${{cpus}}"
echo "[runner] job_dir=${{job_dir}}"
echo "[runner] chunk_csv_src=${{chunk_csv_src}}"
echo "[runner] wrapper_local=${{wrapper_local}}"
echo "[runner] workspace_local=${{workspace_local}}"
echo "[runner] time=$(date -Is)"
echo "[runner] hostname=$(hostname)"

[ -n "$chunk_id" ] || die "missing chunk_id" 2
[ -n "$chunk_csv_src" ] || die "missing chunk_csv path" 2

chunk_csv="$(basename "$chunk_csv_src")"
[ -f "$chunk_csv" ] || die "chunk CSV not found in sandbox: $chunk_csv (from $chunk_csv_src)" 3
[ -f "$wrapper_local" ] || die "wrapper not found in sandbox: $wrapper_local" 3
[ -f "$workspace_local" ] || die "workspace not found in sandbox: $workspace_local" 3

# CMS env
[ -f /cvmfs/cms.cern.ch/cmsset_default.sh ] || die "missing /cvmfs/cms.cern.ch/cmsset_default.sh" 10
export VO_CMS_SW_DIR=/cvmfs/cms.cern.ch
source /cvmfs/cms.cern.ch/cmsset_default.sh
command -v scramv1 >/dev/null 2>&1 || die "scramv1 not found after cmsset_default.sh" 11
[ -d "$cmssw_src" ] || die "cmssw_src not found: $cmssw_src" 12

cd "$cmssw_src" || die "cannot cd to cmssw_src=$cmssw_src" 12
eval "$(scramv1 runtime -sh)" || die "scramv1 runtime failed" 13
command -v combine >/dev/null 2>&1 || die "combine not found in PATH after scram runtime" 14
command -v python3 >/dev/null 2>&1 || die "python3 not found" 15

if [ "{'1' if sanitize_env else '0'}" = "1" ]; then
  unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_SHLVL CONDA_PROMPT_MODIFIER
  unset PYTHONPATH PYTHONHOME PYTHONNOUSERSITE
  export PYTHONNOUSERSITE=1
  unset PERL5LIB
fi

cd "$job_dir" || die "cannot cd back to job_dir=$job_dir" 16

args=( {common_args_str} )
name="${{base_name}}.chunk${{chunk_id}}"

keep_flags=()
if [ "${{keep_point_outputs}}" = "1" ]; then
  keep_flags+=( "--keep-point-outputs" )
fi
if [ "${{keep_workdirs}}" = "1" ]; then
  keep_flags+=( "--keep-workdirs" )
fi

echo "[runner] launching wrapper (name=$name)"
python3 "$wrapper_local" combine "${{args[@]}}" "$workspace_local" \\
  --fromfile "$chunk_csv" \\
  -n "$name" \\
  -j "$cpus" \\
  --hadd \\
  "${{keep_flags[@]}}"
wrap_rc="$?"
[ "$wrap_rc" -eq 0 ] || die "wrapper failed rc=$wrap_rc" 20

expected="higgsCombine${{name}}.${{method}}.mH${{mass}}.root"
[ -f "$expected" ] || die "expected merged output not found: $expected" 21

mv -f "$expected" "$bundle/" || die "cannot move output to bundle" 23

if [ -d "logs" ]; then
  if [ ! -e "$bundle/logs" ]; then
    mv -f "logs" "$bundle/" || true
  fi
fi

echo "[runner] done. Produced $bundle/$(basename "$expected")"
exit 0
"""
    runner_path.write_text(content, encoding="utf-8")
    runner_path.chmod(0o755)


def write_submit_file(
    submit_path: Path,
    runner_path: Path,
    chunk_list_path: Path,
    log_dir: Path,
    cpus_per_job: int,
    request_memory_mb: int,
    job_flavour: str,
    getenv: bool,
    wrapper_src_abs: Path,
    workspace_src_abs: Path,
    username: str,
    inituser: str,
    queue_from: Path,
):
    content = f"""universe                = vanilla
executable              = {runner_path}

Proxy_filename          = x509up
Proxy_path              = /afs/cern.ch/user/{inituser}/{username}/private/$(Proxy_filename)
x509userproxy           = $(Proxy_path)
use_x509userproxy       = true

getenv                  = {"True" if getenv else "False"}

should_transfer_files   = YES
when_to_transfer_output = ON_EXIT
transfer_executable     = True

# Per-job input: $(chunk_csv) plus common inputs
transfer_input_files    = $(chunk_csv), {workspace_src_abs}, {wrapper_src_abs}

# Per-job output: unique bundle directory (created by runner even on failure)
transfer_output_files   = bundle_chunk$(chunk_id)

request_cpus            = {cpus_per_job}
request_memory          = {request_memory_mb}

+JobFlavour             = "{job_flavour}"

log                     = {log_dir}/scan.$(ClusterId).log
output                  = {log_dir}/scan.$(ClusterId).$(ProcId).out
error                   = {log_dir}/scan.$(ClusterId).$(ProcId).err

arguments               = $(chunk_id) $(chunk_csv) {cpus_per_job}

queue chunk_id, chunk_csv from {queue_from}
"""
    submit_path.write_text(content, encoding="utf-8")


# --------------------------
# Post-run helpers
# --------------------------

def load_run_config(run_dir: Path) -> RunConfig:
    cfg_path = run_dir / "RUN_CONFIG.json"
    if not cfg_path.exists():
        raise RuntimeError(f"missing {cfg_path} (did you run initial submission with this script?)")
    data = read_json(cfg_path)
    return RunConfig(**data)


def make_failed_chunks_list(run_dir: Path, cfg: RunConfig) -> tuple[Path, list[int]]:
    chunk_list_path = Path(cfg.chunk_list_path)
    if not chunk_list_path.is_absolute():
        chunk_list_path = (run_dir / chunk_list_path).resolve()

    lines = read_non_empty_lines(chunk_list_path)
    if not lines:
        raise RuntimeError(f"empty chunk list: {chunk_list_path}")

    expected_missing: list[int] = []
    kept_lines: list[str] = []

    for ln in lines:
        parts = ln.split()
        if len(parts) < 2:
            continue
        chunk_id = int(parts[0])
        bundle = run_dir / f"bundle_chunk{chunk_id}"
        expected = bundle / cfg.expected_root_name(chunk_id)

        if (not bundle.exists()) or (not expected.exists()):
            expected_missing.append(chunk_id)
            kept_lines.append(ln)

    out_path = run_dir / "failed_chunks.list"
    out_path.write_text("\n".join(kept_lines) + ("\n" if kept_lines else ""), encoding="utf-8")

    # Also write a simple numeric list for quick greps
    (run_dir / "failed_chunks.ids").write_text(
        "\n".join(str(x) for x in expected_missing) + ("\n" if expected_missing else ""),
        encoding="utf-8",
    )

    return out_path.resolve(), expected_missing


def collect_and_hadd(run_dir: Path, cfg: RunConfig) -> Path:
    out_dir = run_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Copy roots from bundle_chunk*/ into output/
    pattern = f"higgsCombine{cfg.base_name}.chunk*.{cfg.method}.mH{cfg.mass_g}.root"
    bundle_roots = sorted(run_dir.glob(f"bundle_chunk*/{pattern}"))
    if not bundle_roots:
        raise RuntimeError(f"no per-chunk roots found under bundle_chunk*/{pattern}")

    for p in bundle_roots:
        shutil.copy2(p, out_dir / p.name)

    merged = out_dir / f"higgsCombine{cfg.base_name}.ALL.{cfg.method}.mH{cfg.mass_g}.root"

    if shutil.which("hadd") is None:
        raise RuntimeError("hadd not found in PATH")

    # Use hadd with an explicit file list to avoid arg-length issues
    filelist = out_dir / "hadd_inputs.txt"
    filelist.write_text("\n".join(str((out_dir / p.name).resolve()) for p in bundle_roots) + "\n", encoding="utf-8")

    subprocess.check_call(["hadd", "-f", str(merged), f"@{filelist}"], cwd=str(run_dir))
    return merged.resolve()


# --------------------------
# Main
# --------------------------

def main() -> int:
    parser = argparse.ArgumentParser()

    # Main submission args
    parser.add_argument("--cmssw_src", required=True, help="CMSSW src dir where you run scram runtime")
    parser.add_argument("--run_root", required=True, help="parent directory (your extrapoConfigs)")
    parser.add_argument("--run_tag", default="condor_run", help="subdir name under run_root")
    parser.add_argument("--no_clean", action="store_true", help="do NOT delete/recreate run_dir")
    parser.add_argument("--chunks", type=int, default=200)
    parser.add_argument("--threads_per_job", type=int, default=12)
    parser.add_argument("--job_flavour", default="workday")
    parser.add_argument("--request_memory", type=int, default=12000)

    # Env robustness
    parser.add_argument("--getenv", action="store_true", help="set getenv=True in submit file (default: False)")
    parser.add_argument("--no_sanitize_env", action="store_true", help="do NOT sanitize env in runner (default: sanitize)")

    # Output behavior
    parser.add_argument("--keep_point_outputs", action="store_true", help="keep per-point higgsCombine*.root files (default: remove after hadd)")
    parser.add_argument("--keep_workdirs", action="store_true", help="keep work_<name>_<wid>/ directories (default: remove; logs/ is preserved)")

    # Debug subset options (use only one)
    parser.add_argument("--points_first", type=int, default=None)
    parser.add_argument("--points_last", type=int, default=None)
    parser.add_argument("--points_slice", type=str, default=None)
    parser.add_argument("--points_idx", type=str, default=None)
    parser.add_argument("--points_sample", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)

    # Convenience
    parser.add_argument("--debug", action="store_true", help="preset: points_first=20, chunks=10, threads=1, job_flavour=espresso, mem=4000")
    parser.add_argument("--dry_run", action="store_true", help="run all steps except condor_submit")

    # Post-run modes (do NOT require '-- combine ...')
    parser.add_argument("--make_failed_list", action="store_true", help="post-run: generate failed_chunks.list by scanning bundle outputs")
    parser.add_argument("--resubmit_failed", action="store_true", help="post-run: condor_submit condor_fromfile_scan_failed.sub (after making failed list)")
    parser.add_argument("--collect_outputs", action="store_true", help="post-run: copy per-chunk roots into output/ and hadd them")

    args, remainder = parser.parse_known_args()

    run_root = Path(args.run_root).resolve()
    cmssw_src = Path(args.cmssw_src).resolve()
    run_dir = (run_root / args.run_tag).resolve()

    # --------------------------
    # Post-run shortcuts
    # --------------------------
    if args.make_failed_list or args.resubmit_failed or args.collect_outputs:
        cfg = load_run_config(run_dir)

        if args.make_failed_list or args.resubmit_failed:
            failed_list_path, failed_ids = make_failed_chunks_list(run_dir, cfg)
            print(f"[post-run] wrote: {failed_list_path} (failed/missing chunks: {len(failed_ids)})")

        if args.resubmit_failed:
            failed_list = run_dir / "failed_chunks.list"
            if not failed_list.exists() or failed_list.stat().st_size == 0:
                print("[post-run] no failed chunks to resubmit (failed_chunks.list empty/missing).")
                return 0
            sub_failed = run_dir / "condor_fromfile_scan_failed.sub"
            if not sub_failed.exists():
                raise RuntimeError(f"missing {sub_failed}")
            print("[post-run] submitting failed-only...")
            subprocess.check_call(["condor_submit", str(sub_failed)], cwd=str(run_dir))
            print("[post-run] submitted failed-only.")
            return 0

        if args.collect_outputs:
            merged = collect_and_hadd(run_dir, cfg)
            print(f"[post-run] merged file: {merged}")
            return 0

        return 0

    # --------------------------
    # Normal submission path
    # --------------------------
    if args.debug:
        if args.points_first is None and args.points_last is None and args.points_slice is None and args.points_idx is None and args.points_sample is None:
            args.points_first = 20
        if args.chunks == 200:
            args.chunks = 10
        if args.threads_per_job == 12:
            args.threads_per_job = 1
        if args.job_flavour == "workday":
            args.job_flavour = "espresso"
        if args.request_memory == 12000:
            args.request_memory = 4000

    # Require combine command after literal '--' in submission mode
    if "--" not in remainder:
        raise RuntimeError("pass the combine/combineTool command after a literal '--'")
    cmd = remainder[remainder.index("--") + 1 :]
    if not cmd:
        raise RuntimeError("missing command after '--'")
    if cmd[0] not in ("combineTool.py", "combineTool", "combine"):
        raise RuntimeError("expected command starting with 'combineTool.py' or 'combine' after '--'")

    # Create run dir
    if not args.no_clean:
        recreate_dir_from_scratch(run_dir)
    else:
        run_dir.mkdir(parents=True, exist_ok=True)

    chunks_dir = run_dir / "chunks"
    log_dir = run_dir / "condor_logs"
    out_dir = run_dir / "output"
    chunks_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Wrapper (parallel_fromfile_scan.py must exist in run_root)
    wrapper_src = (run_root / "parallel_fromfile_scan.py").resolve()
    if not wrapper_src.exists():
        raise RuntimeError(f"missing wrapper at {wrapper_src} (expected parallel_fromfile_scan.py in run_root)")
    wrapper_path = (run_dir / "parallel_fromfile_scan.py").resolve()
    shutil.copy2(wrapper_src, wrapper_path)
    wrapper_path.chmod(0o755)

    # Parse combine cmd
    method = extract_opt_value(cmd, ["-M", "--method"], default="MultiDimFit")
    mass_raw = extract_opt_value(cmd, ["-m", "--mass"], default="120")
    mass_g = format_mass_g(mass_raw)
    base_name = extract_opt_value(cmd, ["-n"], default="Test")
    fromfile = extract_opt_value(cmd, ["--fromfile"])
    if not fromfile:
        raise RuntimeError("command must include --fromfile <csv>")

    # Workspace: either -d/--datacard or a positional *.root
    ws = extract_opt_value(cmd, ["-d", "--datacard"])
    if ws:
        workspace_path = resolve_path_maybe_relative(run_root, ws)
    else:
        root_candidates = [t for t in cmd if t.endswith(".root")]
        if not root_candidates:
            raise RuntimeError("cannot find workspace .root in command (use -d <ws.root> or pass a .root positional)")
        workspace_path = resolve_path_maybe_relative(run_root, root_candidates[0])

    if not workspace_path.exists():
        raise RuntimeError(f"workspace not found: {workspace_path}")

    csv_path = resolve_path_maybe_relative(run_root, fromfile)
    if not csv_path.exists():
        raise RuntimeError(f"scan csv not found: {csv_path}")

    # Common args for 'combine' (NOT combineTool), to be forwarded to wrapper.
    common_args = cmd[1:]  # drop combineTool.py/combine
    common_args = remove_opts(common_args, ["--fromfile", "-n", "-j", "--hadd", "-d", "--datacard"])
    common_args = [a for a in common_args if a != str(workspace_path) and a != workspace_path.name]

    # Ensure method/mass are included (wrapper extracts them)
    if "-M" not in common_args and "--method" not in common_args:
        common_args += ["-M", method]
    if "-m" not in common_args and "--mass" not in common_args:
        common_args += ["-m", mass_g]

    # Read CSV and apply optional subset selection
    lines = read_non_empty_lines(csv_path)
    if len(lines) < 2:
        raise RuntimeError("csv must contain header + at least one row")
    header = lines[0]
    rows = lines[1:]

    selected_rows, sel_desc = select_rows(
        rows=rows,
        points_first=args.points_first,
        points_last=args.points_last,
        points_slice=args.points_slice,
        points_idx=args.points_idx,
        points_sample=args.points_sample,
        seed=args.seed,
    )

    selected_csv_path = (run_dir / "selected_points.csv").resolve()
    write_selected_csv(header, selected_rows, selected_csv_path)

    prefix = csv_path.stem + "_chunk"
    _, chunk_list_path = split_rows_into_chunks(header, selected_rows, args.chunks, chunks_dir, prefix)

    runner_path = (run_dir / "run_parallel_scan.sh").resolve()
    submit_path = (run_dir / "condor_fromfile_scan.sub").resolve()
    submit_failed_path = (run_dir / "condor_fromfile_scan_failed.sub").resolve()

    write_runner_script(
        runner_path=runner_path,
        cmssw_src=cmssw_src,
        wrapper_src_abs=wrapper_path,
        workspace_src_abs=workspace_path,
        method=method,
        mass_g=mass_g,
        base_name=base_name,
        cpus_per_job=args.threads_per_job,
        common_args=common_args,
        sanitize_env=(not args.no_sanitize_env),
        keep_point_outputs=args.keep_point_outputs,
        keep_workdirs=args.keep_workdirs,
    )

    username = getpass.getuser()
    inituser = username[0]

    # Main submit file queues from chunks.list
    write_submit_file(
        submit_path=submit_path,
        runner_path=runner_path,
        chunk_list_path=chunk_list_path,
        log_dir=log_dir,
        cpus_per_job=args.threads_per_job,
        request_memory_mb=args.request_memory,
        job_flavour=args.job_flavour,
        getenv=args.getenv,
        wrapper_src_abs=wrapper_path,
        workspace_src_abs=workspace_path,
        username=username,
        inituser=inituser,
        queue_from=chunk_list_path,
    )

    # Failed-only submit file queues from failed_chunks.list (generated post-run)
    failed_list = run_dir / "failed_chunks.list"
    if not failed_list.exists():
        failed_list.write_text("", encoding="utf-8")

    write_submit_file(
        submit_path=submit_failed_path,
        runner_path=runner_path,
        chunk_list_path=chunk_list_path,
        log_dir=log_dir,
        cpus_per_job=args.threads_per_job,
        request_memory_mb=args.request_memory,
        job_flavour=args.job_flavour,
        getenv=args.getenv,
        wrapper_src_abs=wrapper_path,
        workspace_src_abs=workspace_path,
        username=username,
        inituser=inituser,
        queue_from=failed_list,
    )

    # Persist run config for post-run actions
    cfg = RunConfig(
        run_dir=str(run_dir),
        cmssw_src=str(cmssw_src),
        base_name=base_name,
        method=method,
        mass_g=mass_g,
        threads_per_job=args.threads_per_job,
        request_memory=args.request_memory,
        job_flavour=args.job_flavour,
        getenv=args.getenv,
        sanitize_env=(not args.no_sanitize_env),
        keep_point_outputs=args.keep_point_outputs,
        keep_workdirs=args.keep_workdirs,
        workspace_path=str(workspace_path),
        wrapper_path=str(wrapper_path),
        selected_csv_path=str(selected_csv_path),
        chunk_list_path=str(chunk_list_path),
    )
    write_json(run_dir / "RUN_CONFIG.json", asdict(cfg))

    print("generated (all inside run_dir):")
    print(f"  run dir:              {run_dir}")
    print(f"  selected csv:         {selected_csv_path} ({sel_desc})")
    print(f"  chunks list:          {chunk_list_path}")
    print(f"  runner script:        {runner_path}")
    print(f"  wrapper (copied):     {wrapper_path}")
    print(f"  submit file:          {submit_path}")
    print(f"  submit failed-only:   {submit_failed_path} (queues from failed_chunks.list)")
    print(f"  logs dir:             {log_dir}")
    print(f"  output dir:           {out_dir}")
    print(f"  cpus/job (= -j):      {args.threads_per_job}")
    print("")
    print("NOTE: each job transfers back: bundle_chunk<ID>/ (contains merged root + logs/ and FAIL_DIAG.txt on crash)")

    if args.dry_run:
        print("\n[dry_run] not submitting. submit manually with:")
        print(f"  cd {run_dir} && condor_submit {submit_path.name}")
        print("\npost-run helper examples:")
        print(f"  python3 {Path(__file__).name} --cmssw_src {cmssw_src} --run_root {run_root} --run_tag {args.run_tag} --make_failed_list")
        print(f"  python3 {Path(__file__).name} --cmssw_src {cmssw_src} --run_root {run_root} --run_tag {args.run_tag} --resubmit_failed")
        print(f"  python3 {Path(__file__).name} --cmssw_src {cmssw_src} --run_root {run_root} --run_tag {args.run_tag} --collect_outputs")
        return 0

    print("\nsubmitting...")
    subprocess.check_call(["condor_submit", str(submit_path)], cwd=str(run_dir))
    print("submitted.")
    print("\nwhen done (optional):")
    print(f"  python3 {Path(__file__).name} --cmssw_src {cmssw_src} --run_root {run_root} --run_tag {args.run_tag} --make_failed_list")
    print(f"  python3 {Path(__file__).name} --cmssw_src {cmssw_src} --run_root {run_root} --run_tag {args.run_tag} --collect_outputs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
