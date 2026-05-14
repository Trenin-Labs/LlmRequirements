# LLM Hardware Benchmarks

Open dataset of consumer and prosumer hardware benchmarks for running large language models locally — throughput, memory headroom, power draw, and regional pricing. Curated by [Trenin Labs](https://llmrequirements.com) and used to power [LLMRequirements.com](https://llmrequirements.com).

**The data is the product.** This repo exists so anyone can audit the numbers behind the site's recommendations, cite specific snapshots, or open a PR with a correction.

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](LICENSE)
&nbsp; ![Last updated](https://img.shields.io/badge/updated-2026--05--14-blue)
&nbsp; ![Builds](https://img.shields.io/badge/builds-54-blue)
&nbsp; ![Models](https://img.shields.io/badge/models-44-blue)
&nbsp; ![Benchmarks](https://img.shields.io/badge/benchmark%20rows-502-blue)

---

## What's in here

| File | Contents |
|---|---|
| [`models.json`](models.json) | 44 open-weights LLMs (Qwen, Llama, Mistral, DeepSeek, GLM, …) with parameter counts, Q4/Q2 disk sizes, VRAM floors and comfort thresholds, and 0–5 ratings on chat / coding / agents / reasoning / long-context / vision. |
| [`builds.json`](builds.json) | 54 hardware builds — Apple Silicon Macs, NVIDIA RTX 3090/4090/5090/Pro 6000, AMD Strix Halo, Intel B60, DGX Spark, tinybox, H100/MI300X servers, etc. Memory, bandwidth, USD MSRP, rig-overhead split, embedded `tps` / `imageSec` / `videoSec` tables. |
| [`benchmarks.json`](benchmarks.json) | Long-format benchmark rows extracted from `builds.json` so they're easy to grep, diff, or load into a dataframe — 330 tps rows, 92 image rows, 80 video rows — plus the 50 source citations behind the numbers. |
| [`useCases.json`](useCases.json) | 8 curated use cases (`coding-agent`, `daily-driver`, `image-gen`, …) with their recommended models and builds. Editorial, but every id resolves into `models.json` / `builds.json`. |
| [`prices/YYYY-MM-DD.json`](prices/) | Weekly snapshots of regional pricing (US/EU/DE/FR/IT/UK/JP …). USD fallbacks plus vendor-direct overrides in local currency, with VAT/consumption-tax baked in where applicable. Diff two snapshots to see how the market moved. |

Everything is plain UTF-8 JSON, pretty-printed, with stable key ordering — so `git diff` is readable and weekly snapshots show a real changelog.

---

## Quick examples

**List every Apple Silicon build, sorted by 70B tokens-per-second:**

```bash
jq '.builds | map(select(.vendor == "Apple")) | sort_by(-(.tps."70b" // 0))
   | .[] | {id, name, tps_70b: .tps."70b", priceUSD}' builds.json
```

**Find every model that fits in 24 GB VRAM with comfort headroom:**

```bash
jq '.models | map(select(.vramComfortQ4 <= 24))
   | .[] | {id, params, vramComfortQ4, ratings: .ratings.coding}' models.json
```

**Cheapest build that can run a 235B-MoE model at all:**

```bash
jq '.builds | map(select(.tps."235b_moe" != null))
   | sort_by(.priceUSD) | .[0] | {id, name, priceUSD, tps_235b: .tps."235b_moe"}' builds.json
```

**Audit pricing changes between two snapshots:**

```bash
diff <(jq -S . prices/2026-05-14.json) <(jq -S . prices/2026-05-07.json)
```

---

## Schema notes (the gotchas)

### `tps` values

- Tokens-per-second, **generation** (`tg`), **single-stream**, **Q4_K_M**, short context.
- Sourced from `llama.cpp` / `vLLM` benchmarks — see `benchmarks.json` → `sources` for the trail.
- `null` means *won't fit* or *no reliable measurement* — distinct from `0`.
- Sizes: `8b`, `14b`, `30b`, `70b`, `120b_moe`, `235b_moe`. MoE entries are active-parameter speed, not dense-equivalent.

### Ratings (0–5)

`0 = N/A · 1 = poor · 2 = ok · 3 = good · 4 = great · 5 = SOTA`.

We are deliberately conservative on `agents`. Sub-200B local models score 30–45% on SWE-rebench resolved-rate — that's `agents: 2` at best. A high `coding` score does **not** imply a high `agents` score. If a number here disagrees with vendor marketing, we'll back it up with a citation in `benchmarks.json → sources` or roll it back.

### `priceUSD` vs `rigOverheadUSD`

`priceUSD` is the whole-system US MSRP. `rigOverheadUSD` is the host-PC slice (PSU, case, mobo, CPU, RAM, storage) that *isn't* the accelerator — so card-only price is `priceUSD − rigOverheadUSD`. Turnkey systems (Macs, DGX Spark, Strix Halo prebuilts, tinybox, OEM workstations) have `rigOverheadUSD: 0`.

Typical overheads: single consumer GPU $600–700, dual $1000–1400, quad homelab $1500–2700, octuple server $2900–3500.

### Pricing snapshots

- Filename is the date the snapshot was taken (ISO-8601, UTC).
- `priceUSD` is *pre-tax* US MSRP.
- EU prices are in EUR with VAT included (≈19%). UK in GBP with 20% VAT. JP in JPY with 10% consumption tax.
- Snapshots are append-only — old ones are never edited. If a vendor retroactively changed a price, we add a new snapshot, not rewrite history.

---

## Contributing

PRs welcome — especially:

- **New benchmarks** with a link to a reproducible source (llama.cpp PR, vLLM run, your own gist with the command line).
- **Corrections** with a citation. "Vendor X says Y" is fine if Y is on vendor X's website today.
- **New builds** that are actually available to buy at the listed price. We don't track paper launches.
- **Region-specific pricing** with a screenshot or vendor URL.

What we won't merge:

- Benchmark numbers without a source.
- Ratings bumped without supporting evidence.
- Affiliate-tagged URLs (this repo is data only — affiliate tagging happens at runtime on the site).
- Pre-release / leaked specs.

Open an issue first if you're proposing a schema change.

---

## Licensing & citation

Released under [CC BY 4.0](LICENSE) — use it, fork it, build on it. Attribution required.

Suggested citation:

> Trenin Labs. *LLM Hardware Benchmarks.* Trenin-Labs/LlmRequirements, snapshot `2026-05-14`. https://github.com/Trenin-Labs/LlmRequirements

Pin to a specific commit if you're citing in a paper or post — schemas evolve and numbers move week to week.

---

## What this repo is *not*

- Not a price comparison site (that's [LLMRequirements.com](https://llmrequirements.com)).
- Not affiliated with NVIDIA, Apple, AMD, Intel, or any model vendor.
- Not the place to ask for buying advice — open a discussion if you have a question about the data, not the decision.
