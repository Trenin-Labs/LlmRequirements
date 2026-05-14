#!/usr/bin/env python3
"""Validate the dataset's structural invariants and cross-references.

Runs in CI (.github/workflows/validate.yml). Exits non-zero on any problem.
Uses only the Python standard library so the workflow needs no install step.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parent.parent

# ---- helpers --------------------------------------------------------------

errors: list[str] = []


def fail(msg: str) -> None:
    errors.append(msg)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        fail(f"{path.relative_to(ROOT)}: invalid JSON — {e}")
        sys.exit(1)


# ---- load ----------------------------------------------------------------

models_doc = load(ROOT / "models.json")
builds_doc = load(ROOT / "builds.json")
benchmarks_doc = load(ROOT / "benchmarks.json")
usecases_doc = load(ROOT / "useCases.json")

price_files = sorted((ROOT / "prices").glob("*.json"))
if not price_files:
    fail("prices/: no snapshot files found")

models = models_doc["models"]
builds = builds_doc["builds"]
use_cases = usecases_doc["useCases"]

model_ids = {m["id"] for m in models}
build_ids = {b["id"] for b in builds}

if len(model_ids) != len(models):
    fail("models.json: duplicate model id(s)")
if len(build_ids) != len(builds):
    fail("builds.json: duplicate build id(s)")

# ---- models --------------------------------------------------------------

MODEL_REQUIRED = {"id", "name", "family", "params", "type", "modality", "ratings"}
RATING_KEYS = {"chat", "coding", "agents", "reasoning", "longContext", "vision"}

for m in models:
    missing = MODEL_REQUIRED - m.keys()
    if missing:
        fail(f"model {m.get('id', '?')}: missing keys {sorted(missing)}")
        continue
    # rating values 0-5
    for k, v in m.get("ratings", {}).items():
        if not isinstance(v, int) or not (0 <= v <= 5):
            fail(f"model {m['id']}: rating {k}={v!r} not an int 0-5")
    # VRAM ordering
    vmin = m.get("vramMinQ4")
    vcom = m.get("vramComfortQ4")
    if vmin is not None and vcom is not None and vmin > vcom:
        fail(f"model {m['id']}: vramMinQ4 ({vmin}) > vramComfortQ4 ({vcom})")
    # MoE sanity
    if m.get("type") == "moe" and "activeParams" not in m:
        fail(f"model {m['id']}: type=moe but missing activeParams")

# ---- builds --------------------------------------------------------------

BUILD_REQUIRED = {"id", "name", "vendor", "category", "memoryGB", "bandwidthGBs", "priceUSD"}

for b in builds:
    missing = BUILD_REQUIRED - b.keys()
    if missing:
        fail(f"build {b.get('id', '?')}: missing keys {sorted(missing)}")
        continue
    if b.get("usableMemoryGB", b["memoryGB"]) > b["memoryGB"]:
        fail(f"build {b['id']}: usableMemoryGB > memoryGB")
    if "rigOverheadUSD" in b and b["rigOverheadUSD"] > b["priceUSD"]:
        fail(f"build {b['id']}: rigOverheadUSD > priceUSD")
    # reviews structural
    for r in b.get("reviews", []):
        vid = r.get("videoId", "")
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", vid):
            fail(f"build {b['id']}: review videoId {vid!r} is not 11 chars")

# ---- benchmarks ----------------------------------------------------------

for row in benchmarks_doc.get("tps", []):
    if row["buildId"] not in build_ids:
        fail(f"benchmarks.tps: unknown buildId {row['buildId']!r}")
for row in benchmarks_doc.get("image", []):
    if row["buildId"] not in build_ids:
        fail(f"benchmarks.image: unknown buildId {row['buildId']!r}")
for row in benchmarks_doc.get("video", []):
    if row["buildId"] not in build_ids:
        fail(f"benchmarks.video: unknown buildId {row['buildId']!r}")

# ---- useCases ------------------------------------------------------------

for uc in use_cases:
    for mid in uc.get("recommendedModels", []):
        if mid not in model_ids:
            fail(f"useCase {uc.get('id')}: recommendedModel {mid!r} not in models.json")
    for bid in uc.get("builds", []):
        if bid not in build_ids:
            fail(f"useCase {uc.get('id')}: build {bid!r} not in builds.json")

# ---- prices --------------------------------------------------------------

date_re = re.compile(r"\d{4}-\d{2}-\d{2}\.json$")
for pf in price_files:
    if not date_re.search(pf.name):
        fail(f"prices/{pf.name}: filename must be YYYY-MM-DD.json")
    doc = load(pf)
    for bid in doc.get("builds", {}):
        if bid not in build_ids:
            fail(f"prices/{pf.name}: unknown buildId {bid!r}")

# ---- affiliate-tag scan --------------------------------------------------

# Public data must not contain affiliate-tagged URLs. Block tag=, BI=, nm_mc=,
# associate=, partner=, ascsubtag=, linkCode=, etc.
AFFILIATE_PARAMS = {
    "tag", "BI", "nm_mc", "associate", "partner", "ref_=as", "ascsubtag",
    "linkCode", "creativeASIN", "ref-suffix",
}
AFFILIATE_HOST_PATTERNS = (
    re.compile(r"amzn\.to"),
    re.compile(r"track\.linksynergy\.com"),
    re.compile(r"go\.skimresources\.com"),
)


def scan_urls(obj, path: str) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan_urls(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            scan_urls(v, f"{path}[{i}]")
    elif isinstance(obj, str) and obj.startswith(("http://", "https://")):
        for pat in AFFILIATE_HOST_PATTERNS:
            if pat.search(obj):
                fail(f"{path}: affiliate-host URL detected — {obj}")
        try:
            qs = parse_qs(urlparse(obj).query, keep_blank_values=True)
        except ValueError:
            return
        leaked = AFFILIATE_PARAMS & qs.keys()
        if leaked:
            fail(f"{path}: affiliate param(s) {sorted(leaked)} in URL — {obj}")


scan_urls(models_doc, "models.json")
scan_urls(builds_doc, "builds.json")
scan_urls(benchmarks_doc, "benchmarks.json")
scan_urls(usecases_doc, "useCases.json")
for pf in price_files:
    scan_urls(load(pf), f"prices/{pf.name}")

# ---- report --------------------------------------------------------------

if errors:
    print(f"Validation failed: {len(errors)} error(s)")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print(
    f"OK — {len(models)} models, {len(builds)} builds, "
    f"{len(benchmarks_doc.get('tps', []))} tps + "
    f"{len(benchmarks_doc.get('image', []))} image + "
    f"{len(benchmarks_doc.get('video', []))} video rows, "
    f"{len(use_cases)} use cases, "
    f"{len(price_files)} price snapshot(s)."
)
