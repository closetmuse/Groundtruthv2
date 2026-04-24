DEEP DIVE — GPU MARKET PRIMER: ARCHITECTURES, USE CASES, PRICING MECHANICS, OBSOLESCENCE
Flagged Sri-direct 2026-04-24  |  Companion to deep_dive_2026-04-24_1130ET_nscale_monarch_btu_to_gpu.md
Written 2026-04-24 11:45 ET  |  Deep dive, not addendum — market-structure reference piece for AI-compute asset class

================================================================
WHY THIS NOW
================================================================

GT has been scoring GPU-hour pricing since Apr 20 as a tape series (H100 SXM, H200, B200, A100) for DC Axis 5 (GPU financing), with Kalshi forward prices as a companion. Alpha-ledger has no GPU-specific finding yet, but DC Axis 5 is developing into an operational axis. The BTU-to-GPU piece (companion deep dive) makes the point that GPU-hour pricing and power-cost floor are coupled at the integrated-operator level. This piece is the reference background for what the GPU stack actually is, how it is priced, how use-case drives demand, and what the obsolescence cycle implies for residual values and financing tenor.

**Audience:** Sri — a project-finance practitioner who sees GPU-related deals cross the desk but has not worked the GPU asset class directly. The goal is to build enough structural fluency to (a) evaluate deal-class fit when a GPU-financing structure appears, (b) understand what is pricing risk vs technology risk vs commodity risk, (c) calibrate residual-value and depreciation assumptions that drive senior-debt sizing.

================================================================
PART 1 — THE GPU LANDSCAPE: WHAT IS ACTUALLY IN THE MARKET
================================================================

The AI-compute accelerator market has three broad architecture families: NVIDIA GPUs (dominant), AMD GPUs (challenger), and custom ASICs from hyperscalers and specialists (Google TPU, AWS Trainium, Microsoft Maia, Cerebras wafer-scale, Groq LPU, Tenstorrent). For practical project-finance purposes, the universe is 85%+ NVIDIA by revenue share as of 2026 and the GPU-financing asset class is predominantly NVIDIA-collateral.

**NVIDIA current-generation training GPUs (Hopper H-series and Blackwell B-series):**

| Name | Arch | Memory | Memory BW | FP16 TFLOPS | FP8 TFLOPS | FP4 TFLOPS | Power (W) | Capex (USD) | Use-case sweet spot |
|---|---|---|---|---|---|---|---|---|---|
| H100 SXM5 | Hopper | 80GB HBM3 | 3.35 TB/s | 989 | 1979 | — | 700 | $25-32k | Large-model training, high-throughput inference |
| H100 PCIe | Hopper | 80GB HBM3 | 2.0 TB/s | 756 | 1513 | — | 350-400 | $20-26k | Cost-sensitive training, inference |
| H200 SXM | Hopper | 141GB HBM3e | 4.8 TB/s | 989 | 1979 | — | 700 | $30-42k | Memory-bound LLM inference (70B-400B models) |
| H20 | Hopper (China-export) | 96GB HBM3 | 4.0 TB/s | 148 | 296 | — | 400 | $12-15k | China-market constrained-compute inference |
| B100 | Blackwell | 192GB HBM3e | 8.0 TB/s | ~1800 | ~3500 | ~7000 | 700 | $30-40k | Blackwell-gen training (low-power variant) |
| B200 | Blackwell | 192GB HBM3e | 8.0 TB/s | ~2250 | ~4500 | ~9000 | 1000 | $40-55k | Frontier training + dense inference |
| GB200 NVL | Blackwell (Grace+Blackwell pair) | 384GB HBM3e (per superchip) | 16 TB/s | ~4500 | ~9000 | ~18000 | 1200-2700 | $60-85k | Top-end frontier training (cluster-native) |
| GB200 NVL72 rack | Blackwell cluster | 13.5 TB HBM3e (72 GPU rack) | — | ~1.4 EFLOPS FP8 | — | — | ~120 kW/rack | $3-4m/rack | Frontier training rack-scale |

**NVIDIA inference-optimized GPUs (L-series, T-series, RTX):**

| Name | Arch | Memory | Memory BW | Power (W) | Capex (USD) | Use-case sweet spot |
|---|---|---|---|---|---|---|
| L40S | Ada Lovelace | 48GB GDDR6 | 0.86 TB/s | 350 | $9-11k | Mid-tier inference, fine-tuning, graphics-adjacent |
| L4 | Ada | 24GB GDDR6 | 0.30 TB/s | 72 | $2.5-3k | Low-power inference (video, embedding) |
| L20 | Ada | 48GB GDDR6 | 0.86 TB/s | 275 | ~$9k | China-market L40 variant |
| A10 | Ampere | 24GB GDDR6 | 0.60 TB/s | 150 | $3-4k | Entry inference, VDI |
| RTX 6000 Ada | Ada | 48GB GDDR6 | 0.96 TB/s | 300 | $6-8k | Workstation / small-cluster inference |
| RTX 4090 | Ada consumer | 24GB GDDR6X | 1.0 TB/s | 450 | $1.6-2.2k | Consumer / dev / small-model inference |
| RTX 5090 | Blackwell consumer | 32GB GDDR7 | 1.8 TB/s | 575 | $2.0-2.5k | Prosumer / dev / small-model |

**Prior-generation training GPUs (still in service):**

| Name | Arch | Memory | Use-case in 2026 | Rental $/hr (Vast.ai range) |
|---|---|---|---|---|
| A100 80GB SXM | Ampere | 80GB HBM2e | Mid-model training, inference, fine-tuning | $0.65-1.20 |
| A100 40GB | Ampere | 40GB HBM2e | Budget inference, fine-tuning, research | $0.40-0.90 |
| A6000 | Ampere workstation | 48GB GDDR6 | Workstation inference, fine-tuning | $0.35-0.70 |
| V100 32GB | Volta | 32GB HBM2 | Legacy inference, academic | $0.25-0.60 |

**AMD MI-series (challenger):**

| Name | Arch | Memory | Memory BW | FP16 TFLOPS | Power (W) | Capex (USD) | Status |
|---|---|---|---|---|---|---|---|
| MI300X | CDNA 3 | 192GB HBM3 | 5.3 TB/s | 1300 | 750 | $15-20k | 2024 flagship, Meta/MS/Oracle adopted |
| MI325X | CDNA 3 refresh | 256GB HBM3e | 6.0 TB/s | 1300 | 1000 | $18-22k | 2025 shipped |
| MI350X/MI355X | CDNA 4 | 288GB HBM3e | 8.0 TB/s | ~2500 | 1000-1400 | — | 2025-26 launch window |
| MI400 | CDNA 5 | 432GB HBM4 (reported) | >13 TB/s | — | — | — | 2026-27 roadmap |

**Custom ASICs (hyperscaler-captive primarily):**

| Name | Owner | Use | Scale | Availability |
|---|---|---|---|---|
| TPU v5p | Google | Training, hyperscaler-internal + limited cloud | 9K-chip pods | GCP rental |
| TPU v6 (Trillium) | Google | Training, hyperscaler-internal | Similar | GCP rental |
| Trainium 2 | AWS | Training/inference, Anthropic anchor | UltraCluster-scale | AWS rental |
| Trainium 3 | AWS | Training (2026) | Expanding | AWS roadmap |
| Inferentia 2 | AWS | Inference only | Broad | AWS rental |
| Maia 100 | Microsoft | Internal training/inference | Azure-internal first | Azure rental limited |
| WSE-3 (Cerebras) | Cerebras | Training (wafer-scale, 900k cores) | On-prem + Cirrascale | Specialty |
| LPU | Groq | Inference only (deterministic latency) | GroqCloud + on-prem | Inference-specialty |

**Takeaway.** The market is architecturally diverse, but **NVIDIA B200 / GB200 / H100 / H200** are the pricing-setting instruments. Everything else prices off that reference set. AMD MI300X-class has credibility but under 15% share; custom ASICs are hyperscaler-captive for their own workloads.

================================================================
PART 2 — HOW TO EVALUATE WHICH GPU FOR WHICH USE CASE
================================================================

**Key technical dimensions that matter for use-case fit:**

1. **Memory capacity (HBM/GDDR).** LLM inference is memory-bound for large models. A 70B-parameter FP16 model is ~140GB; a 175B model is ~350GB; a 400B model is ~800GB. **One GPU's memory determines the largest model that fits before tensor-parallelism across multiple GPUs kicks in.** H200's 141GB single-GPU memory vs H100's 80GB is the structural reason H200 is the preferred GPU for large-model inference. MI300X at 192GB leapfrogged NVIDIA on this dimension; H200 closed much of that gap but not all.

2. **Memory bandwidth.** Inference latency on LLMs is dominated by moving KV-cache and weights through memory. Higher HBM bandwidth = lower inference latency at a given utilization. H200 4.8 TB/s vs H100 3.35 TB/s is ~40% inference throughput uplift on memory-bound workloads. B200 at 8 TB/s is another 67% uplift.

3. **FLOPS at relevant precision.** Training uses FP16/BF16 and increasingly FP8. Inference uses FP8/FP4 (quantized). Blackwell's native FP4 support (FP4 TFLOPS 2x FP8) is the structural reason B200 doubles H100 inference throughput at a similar power envelope.

4. **Power envelope.** H100 700W, B200 1000W, GB200 1200-2700W/superchip. Higher-power GPUs require higher-density cooling (liquid, not air) and put a floor on DC rack power-density. **Older 10-15 kW/rack DC shells cannot host B200/GB200.** This is a real DC-shell obsolescence driver.

5. **Interconnect (NVLink, NVSwitch, InfiniBand).** Training across multiple GPUs requires high-bandwidth GPU-to-GPU links. NVLink domain size (8-GPU HGX → 72-GPU NVL72 with NVSwitch) determines how large a single-cluster model can train without dropping to slower InfiniBand. **For frontier-model training, NVLink domain size is as important as FLOPS.** GB200 NVL72 is the structural answer to 400B+ model training at single-rack density.

6. **CUDA / software stack.** NVIDIA's CUDA stack is the default for ML researchers. AMD's ROCm has closed the gap for LLM inference but still lags for training on custom architectures. **Software-stack switching cost is a real moat for NVIDIA** — enterprises carrying five years of CUDA tooling don't switch easily.

**Use-case fit matrix:**

| Use case | Best GPU | Acceptable alternatives | Why |
|---|---|---|---|
| Frontier foundation-model training (400B+ params) | GB200 NVL72 rack | B200 HGX 8-GPU + IB | NVLink domain + FP4 + HBM capacity |
| Mid-size training (7B-70B params) | H100 SXM | H200, MI300X, B200 if available | HBM + FP8 at known price |
| Fine-tuning pre-trained models | H100 PCIe, A100 80GB | H200 if memory-bound, MI300X | Cost-optimized HBM access |
| High-throughput dense-model inference | B200, H200 | H100 SXM, MI300X | Memory bandwidth for KV-cache |
| Memory-bound large-model inference | H200, MI300X, B200 | H100 only if batch-size allows | HBM capacity structural |
| Mid-tier inference (small-model, 7B-13B) | L40S, H100 PCIe | A100 40GB, MI300X | Cost-per-throughput balance |
| Low-cost inference (embeddings, RAG, small models) | L40S, L4 | A10, RTX 6000 Ada | Power efficiency |
| Edge / embedded inference | L4, Jetson | Custom ASIC | Power envelope |
| Graphics / VDI with AI | RTX 6000 Ada, L40S | A10 | Graphics + compute |
| Dev / prosumer workstation | RTX 5090, RTX 4090 | RTX 6000 Ada | Cost |
| Extreme-latency deterministic inference | Groq LPU, custom ASIC | H100 with software optimization | LPU deterministic latency |
| Training at 900k-core monolithic | Cerebras WSE-3 | Only option | Wafer-scale parallelism |

**Rule of thumb for a project-finance underwriter looking at a new deal:**

- **"Frontier training" cluster** → expect GB200 or B200, 100-300MW site, 120 kW/rack liquid cooling, NVLink-rich interconnect. Capex heavy ($40-80m per 1000 GPU), cluster utilization 85-95% during training runs. Residual value risk is moderate over 4-5 years (still usable for inference after training-generation).

- **"General-purpose inference" cluster** → H100, H200, L40S mix. 20-100MW site, 50-80 kW/rack, air or liquid cooling acceptable. Capex moderate, utilization 60-80% depending on customer mix. Residual value risk higher — inference GPUs commoditize faster on price.

- **"Legacy / budget" cluster** → A100, A10, L4, RTX. 5-30MW site, 10-30 kW/rack, air cooling. Capex already depreciated substantially on secondary market. Utilization variable — often research, academic, or niche-enterprise tenant mix.

================================================================
PART 3 — GPU PRICING MECHANICS: WHAT DOES $1.56/HR ACTUALLY MEAN
================================================================

GPU-hour pricing has three layers worth distinguishing:

**Layer 1 — Primary-market NVIDIA pricing (capex).** NVIDIA sells H100 SXM through OEM channel partners (Supermicro, Dell, HPE, system integrators) at list-price-minus-volume-discount. H100 SXM 8-GPU HGX server unit list-price is around $250-300k; H200 server around $300-400k; B200 server around $400-500k; GB200 NVL72 rack $3-4m. **Primary-market GPU capex is the floor of the asset-class.** Any secondary-market price below capex indicates depreciation, technology obsolescence, or distressed supply.

**Layer 2 — Secondary-market rental / cloud pricing ($/hour).** This is what Vast.ai, Lambda, CoreWeave, RunPod, and other GPU-as-a-service marketplaces publish. GT captures the Vast.ai p50 as the representative spot reference. **Pricing is discovered in a competitive auction-like marketplace where supply is marginal-operator CCGT-powered rigs and grid-connected DC operators; demand is short-tenor compute buyers (researchers, startups, inference-burst workloads).**

Sample GT tape points (Apr 24 2026):
- H100 SXM: $1.564 p50 (spot, n=11 offers) | Kalshi forward KXH100MON $1.755
- H200: $3.535 p50 (spot, n=15) | Kalshi forward $2.545 
- B200: $4.001 p50 (spot, n=18) | Kalshi forward $4.695
- A100 SXM: $0.848 p50 (spot, n=18) | Kalshi forward $0.955

**What the $/hour actually pays for.** The marketplace operator's cost stack per GPU-hour is approximately:
- Depreciation on GPU capex (ex. H100 at $28k over 5-yr useful life, 85% utilization) = $0.75-0.90/hr
- Power (at $0.06-0.10/kWh delivered, ~1 kW per GPU with PUE of 1.15-1.4) = $0.07-0.14/hr
- Server, network, and DC shell allocation (pro-rated) = $0.10-0.20/hr
- Operator gross margin (required to survive) = $0.15-0.30/hr

**Total breakeven at a merchant grid-connected GPU operator: ~$1.30-1.70/hr for H100 SXM.** Current market clearing at $1.56 means the marginal operator is at or slightly above breakeven. This is why short-tenor pricing volatility is high — a 15-20% move above breakeven attracts new supply entry, a 15-20% move below forces operators to cut offerings.

**What changes at a BTU-to-GPU operator (Nscale-class, see companion deep dive).** Power cost drops from $0.07-0.14/hr to $0.02-0.05/hr at captive Marcellus-basis gas CCGT. DC shell cost is internalized vs rented. **Breakeven for BTU-to-GPU operator: ~$0.90-1.20/hr for H100 SXM. Structural floor is 30-45% below merchant peers.**

**Layer 3 — Term-contract pricing (multi-year reserved compute).** Hyperscaler-anchored reserved-compute contracts (CoreWeave-Microsoft, Lambda-hyperscaler, Nscale-Microsoft) price on multi-year commitments. Reserved H100 SXM clears at $1.80-2.40/hr on 1-3 year commitments — higher than spot because the operator bakes in GPU-asset residual-value risk, technology obsolescence, and customer-credit term-premium. **This is the price point that typically supports project-finance senior-debt sizing** — reserved-compute revenue is contracted, banks size debt against it.

**What drives $/hour pricing movement:**

- **Supply additions.** When a new Crusoe / Nscale / Lambda cluster commissions, spot softens 5-15% in the affected region over 2-4 weeks.
- **Training-run demand pulses.** Frontier-model training runs consume thousands of GPUs for weeks-months. When Anthropic, Meta, or OpenAI starts or completes a training run, spot can move 20-50%.
- **Next-gen arrival.** When B200 broad-shipment began Q4 2025, H100 spot fell ~20% as marginal-buyer demand shifted to B200 and some H100 capacity got repositioned to inference.
- **Chip-supply bottlenecks.** TSMC CoWoS packaging capacity and HBM supply (SK Hynix, Samsung, Micron) directly constrain GPU throughput. Any HBM shortage (as in 2024) tightens primary-market delivery and lifts both capex and $/hr spot.
- **Power availability.** Sites with gigawatt-scale power available can deploy clusters; sites without can't. When a region's grid-interconnect bottleneck tightens, regional $/hr firms.
- **Regulatory.** Export-control actions (China H20 only, potential Middle East constraints) directly change addressable demand and secondary-market supply availability.

**Kalshi forward vs spot — what that signal means.** Forward-above-spot (H100 $1.755 vs $1.564, B200 $4.695 vs $4.001, A100 $0.955 vs $0.848) is the market pricing a forward firming. Forward-below-spot (H200 $2.545 vs $3.535) is the market pricing forward softening. **The H200 forward-discount is likely reflecting the expected H200 displacement by B200 for memory-bound inference over the next 6-12 months.** B200 forward-premium is expected undersupply persistence. GT's Kalshi capture cadence will develop into a more reliable forward-curve read over the next 2-4 weeks as marketplace-composition noise settles.

================================================================
PART 4 — WHAT GETS BETTER IN THE FUTURE
================================================================

Multiple vectors of improvement are in flight, each on a different cadence:

**1. Precision-reduction FLOPS throughput (short-cycle, 1-2 years).** Blackwell brought native FP4 support — inference throughput doubled from H100's FP8-native. Next-gen Rubin (2026-27 roadmap) is expected to add FP3 or FP2 experimental support plus further FP4 efficiency. **Each precision reduction roughly doubles inference throughput at similar silicon.** Impact on $/hr: lower FP4 cost-per-token means inference pricing erodes for the same workloads, while training flops continue to require higher precision and hold pricing.

**2. HBM capacity and bandwidth (medium-cycle, 2-4 years).** HBM3e (B200/H200 current) ships at 192GB per GPU; HBM4 (Rubin, MI400) is expected at 288-384GB per GPU with ~40-50% more bandwidth. **Single-GPU memory at 288-384GB lets a single GPU hold a 400B-parameter model in FP4** — eliminating tensor-parallelism for all but frontier-frontier workloads. Impact on $/hr: memory-bound inference pricing compresses further as per-GPU capacity moves to cover the whole deployed model-size distribution.

**3. NVLink domain size and rack density (medium-cycle, 2-4 years).** NVL72 (72-GPU domain) enables 400B+ training without InfiniBand. Future NVL144 or NVL288 architectures would enable 1T+ monolithic training — though by 2028+ foundational models may plateau in parameter count and emphasize compute-per-token rather than parameter-count scaling. Rack-density is moving from 120 kW/rack (GB200 NVL72) toward 240 kW/rack (2027+ roadmap), which is a DC-shell-redesign driver more than a GPU-pricing driver.

**4. Optical / photonic interconnect (medium-long cycle, 3-6 years).** Switching GPU-to-GPU from copper (NVLink today) to optical would add ~2x bandwidth at ~half the power. Early announcements from multiple vendors (NVIDIA, Ayar Labs, Lightmatter) target 2027-29 integration. Impact on $/hr: modest — improves efficiency but changes capex floor upward in parallel.

**5. Alternative architectures (medium-long cycle, 3-5 years).** Google TPU, AWS Trainium, Cerebras, Groq, Tenstorrent continue to take share at workload-specific slivers. If any achieve 20%+ share at a category (like Groq at deterministic-latency inference), NVIDIA pricing-power in that category erodes. **Most likely displacement zone: hyperscaler-internal inference workloads** (Trainium 3, Maia, TPU handle Amazon/Microsoft/Google-internal queries at lower cost).

**6. GPU-as-a-service commoditization (ongoing).** More operators entering (Crusoe, Nscale, Lambda, CoreWeave plus dozens of regional operators). As supply diversifies, $/hr-pricing distribution tightens and average margin compresses. **The alpha shifts from "access to GPUs" (2023-24) to "cost-basis on GPUs" (2026-28) to "differentiated compute service" (2028+).** Integrated BTU-to-GPU operators win the middle window.

**7. Software-stack efficiency (ongoing, highly impactful).** Triton, vLLM, TensorRT-LLM, SGLang, and emerging compilers improve GPU utilization on the same silicon by 20-60% for typical inference workloads. **A generation of software improvement is worth a generation of silicon.** Impact on $/hr: pricing pressure from above on inference as buyers extract more throughput per GPU-hour.

================================================================
PART 5 — WHAT HAPPENS TO OLD GPUs
================================================================

GPU obsolescence is non-linear and worth understanding precisely because it drives residual-value assumption in GPU-financing deals.

**Generation migration pattern (observed):**

- **N generation (current top): frontier training.** GB200/B200 in 2026. Used for training frontier models. 85-95% utilization during active training runs. Premium pricing.
- **N-1 generation (one back): mid-training, high-throughput inference.** H200/H100 SXM currently. Used for fine-tuning, mid-size training, and production inference. 70-85% utilization. Mid-tier pricing.
- **N-2 generation (two back): inference, research, development.** A100 currently. Used for inference (especially memory-bound), fine-tuning, academic research. 50-70% utilization. Heavily discounted vs capex.
- **N-3 generation (three back): long-tail workloads.** V100/A40/A6000 currently. Academic, smaller-enterprise, batch-compute. 30-50% utilization. Deep discount.
- **N-4 and older: salvage.** P100/K80. Hobbyist, decommissioning, scrap. Near-zero residual.

**Depreciation curves (estimated from observed secondary market):**

- Year 1 post-release: 90-95% of original capex retained (scarcity).
- Year 2-3: 65-80% retained (broad deployment peaks).
- Year 4-5: 40-60% retained (next generation shipped broadly).
- Year 6-7: 20-40% retained (two generations newer).
- Year 8+: 5-20% retained (largely salvage).

**Key question: are GPUs 4-year or 6-year assets?** The hyperscalers (Microsoft, Google, Meta, AWS) materially extended GPU useful-life assumptions in their accounting from 4-5 years to 6 years during 2023-25, justified on "software optimization extends effective life" and "inference workloads keep older GPUs productive." Whether this is sustainable or aggressive accounting is open. **For project-finance underwriting, 5-year useful life is the prudent assumption — 6-year is hyperscaler accounting-treatment, not asset-economics.**

**Repurposing pattern:**

1. **Training → inference migration.** When a GPU generation is no longer preferred for training, it cascades into inference. A100 is a prime current example — displaced from training by H100/B200 but still economic for inference workloads. The GPU itself doesn't change; the workload migrates.

2. **Primary market → secondary market.** Hyperscaler/Nscale-class operators buying new H100/H200/B200 occasionally sell down older A100 inventory through secondary-market brokers. Secondary-market A100 in 2026 clears at $8-14k (down from $18-22k primary in 2022), supporting merchant GPU operator entry at lower capex basis.

3. **Utilization vs capex arbitrage.** A merchant GPU operator with $10k A100s running at 70% utilization earning $0.85/hr spot makes roughly $5.2k/year revenue per GPU vs $2.5k/year power+overhead cost = $2.7k/year margin = 27% yield on capex. **This is why older GPUs have extended economic lives — the math works at secondary-market capex even as primary-market prices move to newer silicon.**

**Stranded-asset risk.** Multiple drivers can move a GPU generation from "productive at discount" to "stranded":

- **Power density escalation.** 120 kW/rack Blackwell deployments require liquid cooling. A DC shell originally designed for 10-30 kW/rack air-cooled A100 deployments cannot be easily retrofitted. **The DC shell strands before the GPU strands** in many cases.
- **Interconnect obsolescence.** Older NVLink generations and older InfiniBand (HDR vs NDR vs XDR) become incompatible with mixed clusters. A cluster of 4-year-old A100s can still run but can't easily add GB200s alongside.
- **Software compatibility.** CUDA version support drops for older architectures at some cadence (typically 5-7 years after release). When Ampere architecture drops support in CUDA versions that LLM frameworks standardize on, A100 becomes harder to deploy. **Support-drop timing is a key risk factor for 5+ year-out residual values.**
- **Demand-side workload shifts.** If the industry moves to mixture-of-experts models or dense sparse-activation patterns, older GPUs may be less efficient per model-watt than current expectation.
- **Regulatory stranding.** Export-controlled GPUs (H20 in China) have bifurcated secondary markets. Geopolitical shifts can strand regional inventory.

**Residual-value haircuts for senior-debt sizing.**

Recommended underwriting residual-value assumptions (conservative for PF senior debt):

| Asset | Useful life | 5-yr residual | 7-yr residual |
|---|---|---|---|
| Current-gen B200 | 5-6 years | 30-40% of capex | 10-20% |
| H100/H200 | 5 years | 20-35% of capex | 5-15% |
| A100 | 5 years (already late-cycle) | 10-20% | 0-5% |
| DC shell (100+ kW rack-ready) | 15-20 years | 60-70% | 50-60% |
| DC shell (legacy 10-30 kW rack) | 10 years | 40-50% | 20-30% |
| CCGT BTU-to-GPU captive | 25-30 years | 70-80% | 65-75% |

**Key underwriting implication.** Senior debt against a GPU-cluster asset should amortize faster than senior debt against the DC shell housing it; the shell amortizes faster than the CCGT powering it. **Most project-finance GPU-as-a-service deals should be structured with layered amortization** — rapid pay-down on GPU tranche (4-5 yr), standard PF amortization on shell (15-20 yr), long-tenor on power (20-25 yr).

================================================================
US PROJECT-FINANCE IMPLICATIONS — THE SRI DOMAIN SECTION
================================================================

**Why GPU-financing is becoming a PF asset class.** GPU clusters at multi-hundred-million-dollar capex carried by operators with insufficient corporate credit to absorb the full capex on balance-sheet creates demand for asset-level financing. CoreWeave's high-yield bond issuance, Lambda's equity and debt financings, and emerging private-credit GPU-lease structures all evidence the asset class formation. The Fed's willingness to let this develop (as opposed to prudential concerns about crypto-era GPU lending) is intact as of 2026-04-24.

**Credit layers and who bears which risk.**

1. **GPU hardware (the asset).** Secondary-market liquidity and residual value determine recovery in a stressed scenario. NVIDIA-collateral is the strongest single-asset class; AMD and custom ASICs have narrower secondary markets and should haircut accordingly.
2. **Offtake / revenue contract.** Reserved-compute with a hyperscaler (anchor) vs merchant GPU-hour revenue. Anchor is near-IG; merchant is spread-wide and wrap-eligible (see ALF-19-1).
3. **Operator (sponsor credit).** Nscale, Lambda, CoreWeave — none are rated IG; senior-debt senior to sponsor equity but still subject to sponsor operating skill and solvency.
4. **Facility / power / interconnect risk.** Can the facility deliver power and cooling at contracted spec throughout useful life? BTU-to-GPU operators bear this internally; merchant operators externalize to colo providers.

**Tenor discipline.** GPU-financing tenor should match GPU useful life minus 1-2 years safety. **5-year useful life → 3-4 year senior debt tenor maximum.** 6-year useful life (hyperscaler accounting view) → 5-year senior debt at stretch. Do not stretch senior debt to 7+ years on GPU collateral unless cross-collateralized with shell and power that carry longer-life residual support.

**Structural features to require in a GPU-financing term sheet.**

- **Minimum reserved-compute offtake** against the debt service coverage test, not against cluster revenue. Spot-market revenue upside is available to equity, not levered into the senior tranche.
- **Technology-refresh covenant.** Sponsor commitment to fleet-refresh cadence aligned with useful-life assumption. If sponsor defers refresh, bank can accelerate.
- **Residual-value insurance or wrap** for merchant-class clusters. ILS-wrap (ALF-19-1 mechanism) is developing as a specific tool here.
- **Power-supply assurance / hedging.** For merchant operators, floor on grid-tariff exposure. For BTU-to-GPU operators, CCGT availability and gas-supply counterparty.
- **Sponsor cash-trap tests.** Distribution limitations until senior-debt DSCR ratios cleared for four consecutive quarters.

**Cross-sector implications for the existing 44-deal pipeline.** The pipeline is dominated by contracted LNG, renewables, and DC deals, not pure GPU-financing. But:

- DC deals with GPU-as-a-service offtake structures are appearing (no specific deals named per alpha-not-portfolio-review discipline); the GPU-tenor-vs-shell-tenor question will start arising in underwriting.
- Merchant-class DC deals benefit or suffer based on GPU-spot pricing durability; underwriting scenario analysis should include GPU-hour sensitivity (±30% spot pricing shock).
- Hyperscaler-anchored DC deals are largely insulated from GPU-hour volatility; the hyperscaler is the offtaker regardless of GPU-price movement.

**Watch items for 2026-27 (30-90 day and longer cadence):**

1. First publicly-reported GPU-collateralized private-credit structure inside $500m. Pricing benchmark for the asset class.
2. Kalshi forward-curve maturation on H100/H200/B200 — monthly settles becoming reliable enough to use in PF scenario analysis.
3. Cerebras, Groq, or Trainium-collateral financing emerging. Non-NVIDIA GPU-class asset-financing would be a structural expansion.
4. Any Amazon-Talen-class BTM regulatory setback that affects BTU-to-GPU operators. This is an interconnection/regulatory risk concentrated at the operator tier.
5. Hyperscaler GPU-useful-life accounting revisitations. If hyperscalers extend or shorten the assumption materially, PF underwriting assumptions must recalibrate.

================================================================
CROSS-AXIS THREADING
================================================================

**DC Axis 5 (GPU financing).** Core axis for this piece. All prior framework substrate now has a structural reference. Expect Sunday weekly review to refine DC Axis 5 operational definitions.

**DC Axis 6 (BTM coupling).** BTU-to-GPU operators are simultaneously DC Axis 6 (BTM) and DC Axis 5 (GPU) — the two axes converge at the integrated-operator archetype. Cross-axis reading becomes important.

**DC Axis 7 (ILS-wrapped DC senior debt).** Merchant GPU-financing variants are ILS-wrap-eligible. This piece formalizes the mechanism-level reasoning for why ALF-19-1's structure applies.

**Power Axis 3 (Interconnection).** GPU-cluster power-density escalation (120 kW/rack Blackwell → 240 kW/rack 2027+) is the physical driver of why grid-interconnect is capacity-binding. Larger clusters need more power at one site.

**LNG Axis 1 (HH-JKM arb).** Indirectly — if BTU-to-GPU captures substantial Appalachian gas demand over 2027-30, Gulf Coast LNG feedgas economics compress.

**ALF-20260419-1 (ILS-wrap substrate).** Merchant GPU-financing is a direct consumer of the ALF-19-1 mechanism. Substrate relevance continues.

================================================================
WHAT TO WATCH NEXT 30-90 DAYS
================================================================

1. **GPU-hour spot volatility.** GT captures 4 GPUs daily; a stable baseline emerges 2-4 weeks into data collection. By end-May, variance bands will be tight enough to read signal from noise.

2. **Kalshi forward-market liquidity.** Current Kalshi volumes are thin (nil-vol on most reads). If volume builds, the forward curve becomes a genuine price-discovery tool rather than marketplace-maker quote reference.

3. **B200 broad availability.** Primary-market B200 shipment and delivery cadence through 2026Q2-Q3 affects both H100 residual value (displacement) and B200 spot pricing.

4. **Rubin-generation announcements.** Rubin (2026) and Rubin Ultra (2027) detailed specifications expected mid-2026. These will set next-generation capex levels and reset H200/B200 residual-value expectations.

5. **AMD MI350X/MI400 traction.** If MI400 at 432GB HBM4 ships to hyperscaler anchors (Meta, Microsoft, Oracle continue to show interest), AMD's structural share gain becomes material — pricing pressure on equivalent-tier NVIDIA.

6. **Hyperscaler capex commentary.** Quarterly earnings calls from Microsoft, Google, Meta, AWS discussing GPU useful-life assumptions, capex intensity, and Trainium/Maia/TPU vs NVIDIA mix. These set baseline assumptions for the merchant GPU-operator environment.

7. **GPU-as-a-service private-credit structures.** First publicly disclosed senior-debt or term-loan B on GPU-collateralized assets at scale. Pricing benchmark.

8. **Export-control changes.** China-specific H20 already export-controlled; any expansion to H100 or B200 broad export restrictions would restructure secondary-market supply.

================================================================
ALPHA-LEDGER POSITIONING
================================================================

**No new ALF opened.** This is a reference piece, not a time-bound falsifiable market-price prediction.

**Substrate accumulation:**

- **ALF-20260419-1 (ILS-wrapped DC senior debt):** Merchant GPU-financing is a specific consumer of the wrap structure. The piece clarifies the mechanism of how and why.
- **Candidate ALF-20260420-W2 (DC hyperscaler-stack bifurcation):** GPU-financing deals will sort into the same three credit tiers (hyperscaler-captive / hyperscaler-anchored integrated / merchant). Trifurcation thesis remains queued for Sunday.
- **Operational:** DC Axis 5 development enters the tape-reading-stable phase; spot + forward pricing with 2-4 week baseline will support future candidate-ALF framings about GPU-hour pricing persistence, forward-curve-backwardation vs contango signal, and operator-breakeven-cluster.
- **Forward candidate-ALF (not opened today):** "Merchant GPU-hour pricing at the current $1.50-1.65 H100 SXM level cannot support new-entry merchant operator breakeven economics, implying consolidation toward vertically integrated BTU-to-GPU operators over 2027-28." This is a testable structural-alpha claim that needs 2-3 quarters of pricing history before framing as an ALF.

================================================================

**TAPE TONE for the deep dive: memory-bound, power-floored, tenor-disciplined.**

================================================================
