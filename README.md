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
| [`models.json`](models.json) | Open-weights LLMs (Qwen, Llama, Mistral, DeepSeek, GLM, …) with parameter counts, Q4/Q2 disk sizes, VRAM floors and comfort thresholds, and 0 to 5 ratings on chat / coding / agents / reasoning / long-context / vision. |
| [`builds.json`](builds.json) | Hardware builds including Apple Silicon Macs, NVIDIA RTX 3090/4090/5090/Pro 6000, AMD Strix Halo, Intel B60, DGX Spark, tinybox and server systems. Memory, bandwidth, USD reference price, rig-overhead split and embedded throughput tables. |
| [`benchmarks.json`](benchmarks.json) | Long-format benchmark rows extracted from `builds.json` so they're easy to grep, diff or load into a dataframe, with source citations behind the numbers. |
| [`useCases.json`](useCases.json) | Curated use cases (`coding-agent`, `daily-driver`, `image-gen`, …) with their recommended models and builds. Editorial, but every id resolves into `models.json` or `builds.json`. |
| [`prices/YYYY-MM-DD.json`](prices/) | Append-only snapshots of whole-system USD reference prices and regional offers or estimates in local currency. Newer snapshots can identify newly sourced rows; their date does not reverify every carried value. Compare snapshots alongside their coverage notes. |

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
jq '.models | map(select(.vramComfortQ4 != null and .vramComfortQ4 <= 24))
   | .[] | {id, params, vramComfortQ4, ratings: .ratings.coding}' models.json
```

**Cheapest build that can run a 235B-MoE model at all:**

```bash
jq '.builds | map(select(.tps."235b_moe" != null))
   | sort_by(.priceUSD) | .[0] | {id, name, priceUSD, tps_235b: .tps."235b_moe"}' builds.json
```

**Read the MiniMax runs with all their qualification fields:**

```bash
jq '.modelRuns[] | select(.modelId == "minimax-m3-1-flash-428b-moe")' benchmarks.json
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

### Model-specific `modelRuns`

`benchmarks.json.modelRuns` is separate from the generic `tps` arrays above. Each run retains its model and build IDs, quantization, engine, concurrency, decode throughput, source, status and note, plus context, prefill, cluster and speculative-decoding fields where available. Read the whole record. Do not turn it into a generic Q4 fit or hardware ranking.

The six MiniMax records are source-reported (`claimed`), not independent reproductions. Four use the official checkpoint on four DGX Sparks with TP4, DSpark and FP8 KV. Its 300K configured window is not a measured 300K prompt: the reported prompt depths are 238, 27,452 and 97,259 tokens. The C6 result is aggregate, not single-stream.

Two records belong only to the historical 272B expert-pruned checkpoint pinned in their source URLs, on two RTX PRO 6000 Blackwell GPUs. C32 is aggregate. Those numbers do not describe the current 285B successor, and the retained historical `measuredOn` catalog field is not an independently certified run date. Neither regime establishes a matched hardware comparison. Generic Q4 memory fields and editorial ratings remain unassigned for this model.

### Ratings (0–5)

`0 = N/A · 1 = poor · 2 = ok · 3 = good · 4 = great · 5 = SOTA`.

We are deliberately conservative on `agents`. Sub-200B local models score 30–45% on SWE-rebench resolved-rate — that's `agents: 2` at best. A high `coding` score does **not** imply a high `agents` score. If a number here disagrees with vendor marketing, we'll back it up with a citation in `benchmarks.json → sources` or roll it back.

### `priceUSD` vs `rigOverheadUSD`

`priceUSD` is a whole-system US reference price or estimate, not always an MSRP. `rigOverheadUSD` is the retained host-PC budget component (PSU, case, motherboard, CPU, RAM, storage). For DIY builds, `priceUSD − rigOverheadUSD` is an implied accelerator allowance, not necessarily a current standalone retail quote. Turnkey systems (Macs, DGX Spark, Strix Halo prebuilts, tinybox, OEM workstations) have `rigOverheadUSD: 0`.

Typical overheads: single consumer GPU $600–700, dual $1000–1400, quad homelab $1500–2700, octuple server $2900–3500.


### Named US desktop references in the November 8 snapshot

The Mac mini M4 24 GB reference is one new MCYT4LL/A desktop with 512 GB SSD at $1,399 cash, sold and shipped by DataVision Computer Video on [Amazon US](https://www.amazon.com/dp/B0DLBV145M), observed November 7, without AppleCare+. Stock and free delivery were advertised for Herndon 20170, US. Physical stock, other destinations, final tax, checkout and fulfilment remain unverified. It replaces an unconfirmed $999 reference, not a market minimum.

The dual RTX 3090 profile uses the [Custom Lux PCs CL324325](https://customluxpcs.com/product/dual-rtx-3090/) complete system at $7,999 before destination sales tax, observed November 7. Two certified-refurbished 24 GB GPUs share one new-component Core Ultra 9 285K / 128 GB DDR5-5600 / MSI Z890 MPG Carbon WiFi host with advertised x8/x8, 4 TB NVMe alternatives and a 1600 W PSU. NVLink costs extra and is excluded. SSD brand and OS are unselected. Advertised stock and free US shipping do not verify quantity, allocation, destination eligibility, an accepted order or fulfilment.

This replaces an unconfirmed $3,400 DIY estimate as a named purchase-price reference, not like-for-like inflation, a market minimum or a new benchmark. The bundled cards and host have no separately evidenced split: `rigOverheadUSD: 0` does not mean a free host or establish a card-only price. Existing performance and recipes retain their original source systems and regimes, not measurements or compatibility certification of CL324325. Other prices, national overrides and observations retain their existing evidence dates.

### Pricing snapshots

- Filename is the date the snapshot was taken (ISO-8601, UTC).
- `priceUSD` is a US whole-system reference price or estimate. Tax treatment depends on the underlying offer.
- Regional prices use each region's local currency. Tax and shipping scope depends on the seller and source. The October 2 Italian used-desktop amount is a private seller's asking price with no separately verified tax or shipping guarantee.
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
