DEEP DIVE — GPU MARKET PRIMER: ARCHITECTURES, USE CASES, PRICING MECHANICS, OBSOLESCENCE
Flagged Sri-direct 2026-04-24  |  Companion to deep_dive_2026-04-24_1130ET_nscale_monarch_btu_to_gpu.md
Written 2026-04-24 11:45 ET  |  Deep dive, not addendum — market-structure reference piece for AI-compute asset class

================================================================
WHY THIS NOW
================================================================

GT has been scoring GPU-hour pricing since Apr 20 as a tape series (H100 SXM, H200, B200, A100) for DC Axis 5 (GPU financing), with Kalshi forward prices as a companion. Alpha-ledger has no GPU-specific finding yet, but DC Axis 5 is developing into an operational axis. The BTU-to-GPU piece (companion deep dive) makes the point that GPU-hour pricing and power-cost floor are coupled at the integrated-operator level. This piece is the reference background for what the GPU stack actually is, how it is priced, how use-case drives demand, and what the obsolescence cycle implies for residual values and financing tenor.

**Audience:** Sri — a project-finance practitioner who sees GPU-related deals cross the desk but has not worked the GPU asset class directly. The goal is to build enough structural fluency to (a) evaluate deal-class fit when a GPU-financing structure appears, (b) understand what is pricing risk vs technology risk vs commodity risk, (c) calibrate residual-value and depreciation assumptions that drive senior-debt sizing.

================================================================
PART 0 — KEY CONCEPTS IN PLAIN ENGLISH
================================================================

Before the architecture tables and pricing math, a set of plain-language definitions. The rest of the document assumes these.

**FLOPS (Floating-Point Operations Per Second)** — the raw math-speed of the GPU. One "FLOP" is one arithmetic operation (a multiply or an add) on a decimal number. Modern training GPUs advertise trillions (TFLOPS, 10^12) or quadrillions (PFLOPS, 10^15) per second at various precisions. Think of FLOPS as horsepower on an engine spec sheet: the maximum sustained output under perfect conditions. Real-world utilization of advertised FLOPS is typically 35-55% on cluster workloads (see Part 2A). A GPU advertised at "9,000 TFLOPS FP4" is doing nine quadrillion 4-bit math operations per second at peak.

**HBM (High-Bandwidth Memory)** — the GPU's fast-access working memory, where the AI model's weights and intermediate calculations live during a run. HBM is physically stacked right on top of, or right next to, the GPU die (not in separate sticks like the RAM in a PC). It is the single most expensive component on a modern GPU package — often more than the compute die itself. Measured in:
- **Capacity (GB)** — how big a model fits on one GPU. 80GB (H100) fits a ~40B parameter model in FP16; 288GB (B300) fits ~140B in FP16 or ~560B in FP4.
- **Bandwidth (TB/s)** — how fast data can move from HBM into the compute cores. Large-model inference is bandwidth-bound, not compute-bound — which is why H200 (4.8 TB/s) is meaningfully faster than H100 (3.35 TB/s) at inference despite identical compute horsepower.

Think of HBM as the workbench right next to the engine: bigger workbench = bigger job fits, faster workbench access = less time the engine sits idle waiting for parts.

**NVLink / NVSwitch** — NVIDIA's high-speed direct-connect wire between GPUs inside a rack. Lets a group of GPUs act as a single virtual "super-GPU" for training purposes, sharing memory and coordinating compute without routing through standard network gear. A GB200 NVL72 rack is 72 GPUs linked by NVLink through NVSwitch chips. NVLink is the reason training clusters can scale to 72 or 144 or 576 GPUs acting as one. Bandwidth is measured in TB/s per GPU (~1.8 TB/s on current generation). Think of NVLink as private high-speed rail between engines inside an industrial complex — engines work independently but the rail lets them lift a load together without waiting for highway traffic.

**InfiniBand and Ethernet fabric** — the slower, longer-distance network that connects NVLink-rack to NVLink-rack. When a training job exceeds a single NVLink rack (1,000+ GPUs), racks talk to each other over InfiniBand (NVIDIA's Quantum, 400-800 Gbps) or high-end Ethernet. Bandwidth drops by an order of magnitude vs NVLink. This is why NVLink domain size (72 → 144 → 576) is commercially important — bigger domain = more work done without the InfiniBand bottleneck.

**CUDA, ROCm, XLA, Neuron — the software stacks.** Each vendor has its own software layer that translates high-level AI code (PyTorch, TensorFlow) into the specific GPU's instructions:
- **CUDA** — NVIDIA. Industry standard since ~2008. Millions of engineer-hours of tooling built on it.
- **ROCm** — AMD. Functionally comparable for most models; less mature tooling, smaller community.
- **XLA** — Google TPU stack.
- **Neuron SDK** — AWS Trainium/Inferentia.
- **Others** — Intel oneAPI, Cerebras, Groq compiler, etc.

Software written for one stack does not directly run on another — see Part 2A on stranded FLOPS. This is the single largest source of vendor lock-in in the AI-compute ecosystem.

**Precision (FP32 / FP16 / BF16 / FP8 / FP4)** — how many bits the GPU uses to store each number during a calculation. Lower precision means faster math and less memory, with a small accuracy cost:
- **FP32** (32-bit) — full precision, rarely used today outside scientific computing.
- **FP16 / BF16** (16-bit) — training standard through ~2023.
- **FP8** (8-bit) — Hopper/Blackwell training standard.
- **FP4** (4-bit) — Blackwell inference standard, Rubin training experimental.
- **FP2** — Rubin Ultra experimental.

Each halving of precision roughly doubles throughput on the same silicon. Inference tolerates lower precision than training.

**Die, package, rack, pod — the physical hierarchy.** A *die* is one chip wafer cut from a semiconductor manufacturing line (TSMC, Samsung). A *package* is one or more dies plus HBM memory stacks wire-bonded together into a single unit that plugs into a server — the thing that is sold as "a GPU." A *server* (HGX baseboard) holds 8 packages. A *rack* holds 4-9 servers plus networking and cooling — or, in the NVL72 configuration, a single 72-GPU coherent unit. A *pod* or *cluster* holds multiple racks, connected by InfiniBand.

**Training vs inference.** Two fundamentally different workloads:
- **Training** — the expensive process of building an AI model from scratch. Requires frontier silicon (GB200, GB300, Rubin) with rich NVLink and high precision. Costs hundreds of millions to billions of dollars per frontier model. Takes weeks to months. Peak utilization of the cluster for the duration of the run.
- **Inference** — using the trained model to serve user queries. Cheaper per query, spreads across many smaller GPUs (or many instances of larger GPUs). H100, H200, B200, L40S all viable. Utilization is uneven — depends on query load.

Most GPU deployments eventually end up running inference, even if purchased for training. This is the primary residual-value mechanism for older generations (A100, now running inference workloads originally targeted at H100).

**KV cache** — the "key-value" cache, intermediate memory used during inference so the model doesn't recompute the attention values for previously-seen tokens. Grows with conversation length. A 1-million-token context can require 50-150 GB of KV cache *in addition* to the model weights. **This is the primary reason long-context inference workloads need high HBM capacity** — and why H200 (141 GB) and B300 (288 GB) are priced at a premium for inference.

**Tensor parallelism, pipeline parallelism, data parallelism.** Three ways to split a large training run across multiple GPUs:
- **Data parallelism** — each GPU gets a copy of the model, different data slices; gradients combined after each step. Cheap communication.
- **Tensor parallelism** — each GPU holds part of each layer; heavy communication between GPUs inside a layer. Needs NVLink.
- **Pipeline parallelism** — each GPU holds different layers; tokens flow through the pipeline. Moderate communication, needs careful balancing.

Real training runs mix all three. **NVLink domain size determines how much tensor parallelism is economically feasible** — beyond the NVLink domain, tensor parallelism has to traverse InfiniBand, killing throughput.

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

**NVIDIA Blackwell Ultra (GB300 refresh, 2025H2-2026 ship):**

| Name | Arch | Memory | Memory BW | FP16 TFLOPS | FP8 TFLOPS | FP4 TFLOPS | Power (W) | Capex (USD) | Use-case sweet spot |
|---|---|---|---|---|---|---|---|---|---|
| B300 | Blackwell Ultra | 288GB HBM3e | ~8.0 TB/s | ~2500 | ~5000 | ~15000 | 1400 | $50-65k | Memory-scaled inference + training refresh |
| GB300 NVL | Blackwell Ultra (Grace+B300 pair) | 576GB HBM3e (per superchip) | 16 TB/s | ~5000 | ~10000 | ~30000 | 1400-2800 | $70-95k | Long-context frontier workloads |
| GB300 NVL72 rack | Blackwell Ultra cluster | 20.7 TB HBM3e (72 GPU rack) | — | ~1.1 EFLOPS FP8 / ~3.3 EFLOPS FP4 | — | — | ~140 kW/rack | $3.5-4.5m/rack | Top rack-scale frontier (current flagship) |

**Why GB300 matters vs GB200 specifically.** Blackwell Ultra is a within-generation memory + FP4 refresh rather than a new architecture. Memory capacity per GPU jumps from 192GB (B200) to 288GB (B300), a 50% lift — that is the structural feature driving adoption. Single-GPU 288GB fits a 400-500B parameter model in FP4 without tensor-parallelism, and doubles KV-cache headroom for long-context inference (the 1M-token-context workloads that became operationally common through 2025). FP4 throughput also scales ~1.5x, which is the second commercial vector. Power envelope moves up to 1400W per GPU from 1000W (B200) — liquid cooling is mandatory, not optional, at rack scale. **Practical deployment impact:** existing GB200 NVL72 orders placed in 2025 that have not yet shipped are being converted to GB300 NVL72 where hyperscaler offtake agreements permit; the B200 → B300 substitution is narrowing B200's addressable production window to mostly 2025-delivered units.

**NVIDIA Rubin — next architecture (2026 launch, Vera Rubin platform):**

| Name | Arch | Memory | Memory BW | FP4 TFLOPS (est) | Power (W) | Capex (USD est) | Ship window |
|---|---|---|---|---|---|---|---|
| R100 / R200 | Rubin | 288GB HBM4 (initial) | ~13 TB/s | ~20000-25000 | ~1800 | $50-70k | 2026H2 targeted |
| VR200 / Vera Rubin superchip | Rubin + Vera CPU | 576GB HBM4 (per superchip) | ~26 TB/s | ~40000-50000 | 2000-3600 | $80-110k | 2026H2-2027H1 |
| Vera Rubin NVL144 rack | Rubin cluster (144 GPUs) | ~75 TB HBM4 (rack) | — | ~3.6 EFLOPS FP4 (est) | ~180-200 kW/rack | $5-6.5m/rack (est) | 2026H2-2027H1 |
| Rubin Ultra (R300 class) | Rubin Ultra | 1024GB HBM4e (16-stack package per GPU) | ~32 TB/s | ~50000+ | ~3600 | $100-130k (est) | 2027H2 |
| Vera Rubin Ultra NVL576 rack | Rubin Ultra cluster (576 GPUs) | ~365 TB HBM4e (rack) | — | ~15 EFLOPS FP4 (est) | ~600 kW/rack | $15-20m/rack (est) | 2027H2 |

**Vera CPU — the other half of the platform.** Vera is the Rubin-generation ARM CPU successor to Grace. Grace+Blackwell (GB200/GB300) pairs an ARM-based Grace CPU with two Blackwell GPUs through NVLink-C2C coherent interconnect. Vera+Rubin (VR100/VR200) keeps the same template but moves the CPU to a newer custom ARM core with higher memory bandwidth to the GPU pair. For project-finance purposes the CPU is a small share of rack capex (low-single-digit percent) — the Vera distinction matters for internal bandwidth and for the NVL rack architecture but not for residual-value-bearing silicon content.

**Why Rubin matters — the structural jumps.**

1. **HBM4 memory generation.** HBM4 targets ~2 TB/s per stack (vs HBM3e ~1.25-1.4 TB/s per stack), and Rubin's 8-stack package lifts per-GPU memory bandwidth to ~13 TB/s — the 62% lift vs B200's 8 TB/s. Rubin Ultra's 16-stack package doubles that again. **Memory bandwidth is the inference-latency bottleneck; each HBM generation resets the $/hr inference pricing floor.**

2. **FP4 (and experimental FP2/FP6) throughput.** Rubin FP4 throughput ~20000-25000 TFLOPS is ~2-3x B200, ~1.5-2x B300. Inference cost-per-token compresses further at this level; training flops at higher precision get a more modest lift (~40-60%).

3. **NVL144 → NVL576 rack scaling.** NVL144 (144 GPUs per rack, double GB200/GB300's 72) doubles the NVLink domain size in one generation, enabling single-rack training of much larger monolithic models without dropping to InfiniBand between racks. Rubin Ultra's NVL576 quadruples again — 576-GPU single NVLink-coherent domain is a new architectural regime.

4. **Power and cooling.** NVL144 at ~180-200 kW/rack and NVL576 at ~600 kW/rack push DC-shell requirements further up. **The DC shells being built today (120 kW/rack for GB200 NVL72 spec) are already undersized for Rubin Ultra.** Nscale-class integrated operators with ability to iterate on shell design during construction have a real advantage here over colo tenants locked into pre-Rubin rack specs.

5. **Timing implication for current-gen residual.** Rubin broad availability 2026H2-2027H1 means H100/H200/B200 residual-value curves adjust downward from prior expectation starting late-2026. B300 sits awkwardly — a 6-12 month window between broad B300 ship (2025H2-2026H1) and first Rubin volume (2026H2) means **B300 may have the shortest useful-life top-tier window of any Blackwell SKU**, absent explicit hyperscaler anchor contracts that lock the lifetime utilization.

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
PART 2A — STRANDED FLOPS AND WORKLOAD PORTABILITY: THE CUDA MOAT AND WHY DC CAPACITY GETS WASTED
================================================================

The core observation (per recent commentary from Anj Midha on podcast): **paper FLOPS across different GPU architectures are not fungible from a workload perspective.** A 2,000 TFLOPS AMD MI300X is not a drop-in substitute for a 2,000 TFLOPS NVIDIA H100 for most training or inference pipelines, even though the headline compute number is comparable. This shows up at the DC level as capacity under-utilization — sizable blocks of silicon can sit idle or below-peak because the workloads queued don't map efficiently onto the silicon available. As architectures proliferate, this problem is getting worse, not better.

**Why FLOPS are not portable across architectures:**

1. **Compiler-and-runtime lock-in.** A training run optimized for H100 uses CUDA + cuDNN (compute libraries) + NCCL (collective operations) + TensorRT-LLM or vLLM (inference serving) — all NVIDIA-specific. Porting the same run to MI300X requires AMD's equivalents: ROCm + MIOpen + RCCL + AMD's serving stack. **The model will "run" on both — that is the low bar — but peak-throughput performance on the new architecture typically requires 2-6 months of senior engineering investment per model per target.** Without that investment, effective throughput is often 30-60% of nameplate on the non-native architecture.

2. **Tensor layouts and numerical formats differ.** Blackwell's native FP4 format is not bit-compatible with AMD's MXFP4, which is not bit-compatible with Trainium's numerical formats or TPU's BF16-centric stack. Quantizing a model for one architecture and then re-deploying on another means re-quantizing, re-calibrating, and re-validating — weeks of accuracy and performance work, with occasional surprises where a model behaves differently on the new format.

3. **Collective-operation implementations differ.** When 8 or 72 or 1,000 GPUs coordinate on a single training step, they perform *collective operations* — all-reduce (combine all gradients), all-gather (broadcast activations), reduce-scatter (partition and combine). NVIDIA's NCCL is the reference implementation over NVLink + NVSwitch. AMD's RCCL runs over Infinity Fabric. AWS Trainium uses its own NeuronLink-native collectives. Each has different performance characteristics, different edge-case behavior, and different optimal message sizes. **A training run tuned for NVLink topology will perform predictably worse on Infinity Fabric even with careful porting** — not because AMD is slower, but because the tuning is architecture-specific.

4. **Cluster topology is vendor-locked.** A GB200 NVL72 rack cannot accept MI300X sleds. Trainium UltraClusters cannot mix NVIDIA cards. Even *within* NVIDIA generations: a GB300 NVL72 rack is not field-upgradable to Vera Rubin NVL144 — the chassis, power backplane, NVSwitch generation, and cooling loops are generation-locked. **You cannot purchase DC capacity generically and swap silicon in and out** the way you might with commodity x86 server racks. A rack is a single-generation single-vendor asset for its useful life.

5. **Inference-serving stack lock-in.** A production model deployed on H100 through TensorRT-LLM cannot run on Trainium without recompilation via AWS Neuron SDK; cannot run on TPU without XLA; cannot run on Groq without the Groq compiler. Each target platform is a separate deployment-engineering project, with its own testing, monitoring, and on-call implications. For a company with meaningful inference traffic, multi-platform serving is a strategic choice, not a tactical redeployment.

**How workloads move across architectures — the portability gradient:**

| Level | Portability | Effort to move |
|---|---|---|
| **PyTorch / TensorFlow source code** | High | Modest code changes; most models run on NVIDIA, AMD, TPU, Trainium |
| **Trained-weights checkpoint** | Medium | Quantization re-calibration, tolerance testing |
| **Peak-throughput production deployment** | Low | 2-6 months senior engineering per model per target |
| **Multi-GPU training cluster at scale** | Very low | Months-quarters of re-tuning; often impossible without vendor assistance |
| **Hardware topology (rack → rack)** | None | The rack is the unit; replace, not migrate |

**How this strands DC capacity — the four specific mechanisms:**

1. **Offtake-architecture mismatch.** An operator builds 200 MW of Trainium capacity to serve an Anthropic training anchor. Anthropic's next frontier model migrates to a different silicon stack (NVIDIA, for example). The Trainium capacity is not wasted in absolute terms — it can serve inference — but the frontier-training capacity planned-for is no longer the training capacity needed. The sponsor bears the re-routing cost; inference revenue clears at lower $/hr than training reserved-compute.

2. **Rack-composition lock.** Once a rack is built out as GB200 NVL72, it is a GB200 asset for its useful life. A hyperscaler cannot blend a 20% Rubin / 80% B200 workload inside the same NVLink domain. Refreshing a production cluster to a new generation means building new racks, not upgrading cards. **Refresh capex is 60-80% of original DC capex, not 20-40% on the chip line alone** — this is the single most underestimated number in early GPU-financing underwriting.

3. **Power and cooling design locked to silicon generation.** Liquid cooling loops are sized for specific rack-power envelopes. A shell built to 120 kW/rack GB200 spec cannot host 600 kW/rack Rubin Ultra without gutting the cooling infrastructure and upgrading power distribution. **DC shells are silicon-generation-locked in practice** — not formally, but economically. This is the structural reason the DC shell residual-value table (Part 5) bifurcates hard between "Rubin-Ultra-ready" and "legacy" shells.

4. **Inference-platform fragmentation.** A hyperscaler running three or four accelerator stacks internally (NVIDIA, Trainium, TPU, Maia, plus MI300X) cannot load-balance queries across them transparently. Each workload pre-commits to one stack and is served there. **Spare capacity on one stack does not transparently translate to relief on another stack at peak demand.** Effective aggregate utilization across a multi-architecture pool is always below what a single-architecture pool of equivalent aggregate FLOPS would achieve.

**The stranded-FLOPS numeric.** Industry estimates (informal consensus from public commentary through 2025-26) suggest that at cluster level, effective utilization of rated GPU FLOPS averages 35-55% over a year — the balance lost to:
- **Software inefficiency** (kernels below peak, memory-bandwidth bound workloads): 15-25%
- **Network and collective-ops overhead**: 10-15%
- **Idle time between jobs, maintenance, failures**: 5-15%
- **Architectural-mismatch reallocation friction** (the Anj Midha observation): 5-15%, and rising

The fourth item is the one that proliferates with architecture diversity. **In 2023, the installed base was dominated by A100 and H100 — effectively one software target. In 2026, the live installed base includes Hopper (H100/H200/H20), Blackwell (B100/B200/GB200), Blackwell Ultra (B300/GB300), AMD (MI300X/MI325X/MI350X), Trainium 2/3, TPU v5p/v6, Maia, Groq — and Rubin ships in 2026H2.** Each additional architecture reduces the effective fungibility of the aggregate compute pool. A cluster operator managing five architectures runs less effective compute than the sum of nameplate FLOPS would suggest, even at high nominal utilization per pool.

**Why this is hard to fix:**

- **CUDA is the deepest moat in the industry.** PyTorch, TensorFlow, and every major ML framework target CUDA first; AMD, Google, and AWS targets second or later. The network-effect advantage compounds: more CUDA-trained engineers → more CUDA-optimized libraries → more PyTorch kernels tuned for NVIDIA → more models built for NVIDIA → more demand for NVIDIA → more hiring of CUDA-trained engineers. Breaking this is a 5-10 year industry project, not a single-product move.
- **Vendor-neutral abstractions have not worked.** OpenAI's Triton, OpenXLA, MLIR-based approaches, and various cross-vendor compiler projects exist. None have achieved peak-throughput parity across architectures at the pace that would actually make FLOPS fungible. The gap between "code runs" and "code runs at peak" remains the strategic moat.
- **Hyperscalers have mixed incentives.** Google, AWS, Microsoft all want their custom silicon (TPU, Trainium, Maia) to capture internal workloads — that's why they built them. They are not champions of cross-architecture fungibility. NVIDIA obviously isn't either. The only pure champions are operators that stand to benefit from commoditization — merchant GPU operators, some academic and research institutions, and downstream buyers.
- **Standardization would require synchronized capex cycles** across NVIDIA, AMD, hyperscalers, and specialty silicon vendors — a coordination problem with no natural convening authority.

**Implications for project finance:**

- **Concentration risk quantifies differently.** A DC deal with 100% Rubin silicon and a hyperscaler anchor is paradoxically less "stranded" than a diversified-silicon DC serving a merchant customer pool — the former has offtake contracted to the architecture, the latter depends on marginal-customer willingness to run on whatever silicon is available. **Single-architecture + hyperscaler-anchor is a feature, not a bug, under this lens.**
- **Residual value is coupled to software-stack currency.** If NVIDIA drops CUDA-version support for older architectures (typical 5-7 years post-release), older silicon strands economically faster than hardware-physics-based depreciation curves would suggest. **CUDA-lifecycle risk is a first-order input to GPU residual-value underwriting** — not a secondary technology-risk item.
- **Cluster-scale diversification is value-destructive at production peak.** A merchant DC with 30 MW A100 + 40 MW H100 + 60 MW B200 + 100 MW Rubin is not 230 MW of fungible compute — it is four separate compute pools with narrow workload substitution between them. **Senior-debt sizing should reflect the narrower of (a) aggregate offtake revenue, (b) architecture-pool-by-architecture-pool utilization under realistic mismatch assumptions.**
- **Refresh-cycle budgeting must include shell and power.** Capex for silicon refresh must budget rack, cooling, and network refresh at each generation change — not incremental-chip replacement. True refresh capex is 60-80% of original DC capex. **Senior-debt amortization schedules that assume "chip refresh only" are under-sizing the re-investment requirement.**
- **Multi-vendor hedge is operationally expensive.** Traditional infrastructure underwriting benefits from multi-vendor sourcing (two gas-turbine OEMs, multiple inverter suppliers) — it reduces concentration risk. In GPU stacks, multi-vendor is operationally expensive and reduces effective utilization. **The obvious risk-management instinct is actively value-destructive for peak-performance AI-compute operations.** Underwriters need to resist the default "diversification is good" reflex; concentration can be optimal here, offset by hyperscaler-anchor and covenant-level protections.
- **BTU-to-GPU (integrated) operators benefit disproportionately.** Vertically integrated operators like Nscale can plan silicon generation, DC-shell spec, power delivery, and cooling infrastructure as a single design problem, locked to a single hyperscaler anchor and a single architecture. **The integrated architecture model dramatically reduces the stranded-FLOPS risk** relative to colo or merchant models that have to serve heterogeneous silicon and customers. This is an additional structural advantage layered on the cost-basis arbitrage from the companion Nscale deep dive.

**Forward observation.** If Rubin Ultra ships on schedule in 2027H2 and proves to be materially faster per-dollar than GB300 on frontier training, **a large fraction of GB200/GB300 installed base will transition from training duty to inference duty within 12-18 months of Rubin Ultra broad ship** — the software stack will still work, but frontier-training economics will favor the new silicon. DC shells that were designed for 120-140 kW/rack with 5-7 year intended training horizons may effectively age out of training duty in 2028-29, 2-3 years earlier than design-life. **The silicon obsolescence cascade outruns the shell-design horizon.** This is a real risk to DC-shell senior-debt tenor assumptions that project-finance underwriters have not yet fully internalized.

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

**1. Precision-reduction FLOPS throughput (short-cycle, 1-2 years).** Blackwell brought native FP4 support — inference throughput doubled from H100's FP8-native. Blackwell Ultra (GB300) is lifting FP4 throughput another ~1.5x within the same architecture. Rubin (2026H2) adds a further ~2x FP4 lift and is expected to bring experimental FP3 or FP2 paths for inference; Rubin Ultra (2027H2) stacks more memory and packaging changes on top. **Each precision reduction roughly doubles inference throughput at similar silicon.** Impact on $/hr: lower FP4 cost-per-token means inference pricing erodes for the same workloads, while training flops continue to require higher precision and hold pricing.

**2. HBM capacity and bandwidth (medium-cycle, 2-4 years).** HBM3e progression already runs from 141GB (H200) → 192GB (B200) → 288GB (B300). HBM4 on Rubin starts at 288GB per GPU with ~13 TB/s per-GPU bandwidth; Rubin Ultra's 16-stack package targets ~1 TB HBM4e per GPU at ~32 TB/s. **Single-GPU memory at 288-1024GB eliminates tensor-parallelism for all but frontier-frontier workloads** — a 1T-parameter model fits in FP4 on a single Rubin Ultra GPU without cross-GPU sharding. Impact on $/hr: memory-bound inference pricing compresses sharply as per-GPU capacity moves to cover the whole deployed model-size distribution; H200-class memory capacity becomes commodity inference fare within 18-24 months.

**3. NVLink domain size and rack density (medium-cycle, 2-4 years).** NVL72 (72-GPU domain, GB200/GB300) enables 400B+ training without InfiniBand. **Vera Rubin NVL144 (144-GPU domain, 2026H2-2027H1) doubles that.** Rubin Ultra NVL576 (576-GPU domain, 2027H2) quadruples again — a new architectural regime where single-rack NVLink-coherent training spans 576 GPUs. By Rubin Ultra, training cluster topology shifts from "rack + IB fabric" to "rack is the training unit." Rack-density follows: 120 kW/rack (GB200 NVL72) → ~140 kW/rack (GB300 NVL72) → ~180-200 kW/rack (Vera Rubin NVL144) → ~600 kW/rack (Rubin Ultra NVL576). **DC shells permitted and built in 2025 for GB200 specs are already sub-spec for Rubin Ultra** — a structural DC-shell obsolescence driver for 2027-28 refreshes.

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
| Rubin Ultra (2027H2 class) | 5-6 years | 35-45% of capex | 15-25% |
| Rubin R100/R200 (2026H2 class) | 5 years | 30-40% | 10-20% |
| Blackwell Ultra B300 / GB300 | 4-5 years (shortened by Rubin arrival) | 20-30% | 5-12% |
| Blackwell B200 / GB200 | 5 years | 25-35% | 8-15% |
| H100 / H200 | 5 years | 15-30% | 5-12% |
| A100 | 5 years (already late-cycle) | 10-20% | 0-5% |
| DC shell (Rubin-Ultra-ready, 600 kW/rack, liquid) | 20-25 years | 65-75% | 55-65% |
| DC shell (GB200-ready, 120 kW/rack, liquid) | 15-20 years | 55-65% | 45-55% |
| DC shell (legacy 10-30 kW rack, air) | 10 years | 40-50% | 20-30% |
| CCGT BTU-to-GPU captive | 25-30 years | 70-80% | 65-75% |

**B300 residual-value note.** Blackwell Ultra carries a specifically tighter residual-value window because Rubin broad shipment arrives 6-12 months behind B300. **A 2026 H1 B300 purchase has an effective "top-tier" window of only 12-18 months before Rubin displaces it from new-training duty into inference.** For senior-debt sizing, assume a shortened useful life (4-5 years rather than 5-6) on B300 collateral absent hyperscaler-anchor offtake that contractually pins the utilization through year 5.

**Key underwriting implication.** Senior debt against a GPU-cluster asset should amortize faster than senior debt against the DC shell housing it; the shell amortizes faster than the CCGT powering it. **Most project-finance GPU-as-a-service deals should be structured with layered amortization** — rapid pay-down on GPU tranche (4-5 yr, tighter on B300), standard PF amortization on shell (15-20 yr; 20-25 yr on Rubin-Ultra-ready shells), long-tenor on power (20-25 yr).

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

3. **B200 broad availability and B300 ramp.** Primary-market B200 shipment is now tailing off as the GB300 NVL72 production line takes priority; B300 volume-ship cadence through 2026Q1-Q3 affects both H100/H200 residual value (displacement into inference) and B200 spot pricing (early obsolescence vs Rubin).

4. **Rubin ramp (2026H2) and Vera Rubin NVL144 first shipments.** Primary signal: first Vera Rubin NVL144 rack delivery to a hyperscaler anchor. Secondary: Rubin primary-market capex level at volume — this sets the reset point for all down-generation residual-value curves. Tertiary: any slip in Rubin ship window (from 2026H2 to 2027H1) tightens B300's useful-life window further.

5. **Rubin Ultra (2027H2) detailed spec disclosure.** NVL576 rack power envelope (~600 kW/rack expected) and HBM4e memory-per-GPU (~1 TB targeted) set the ceiling for the next DC-shell design generation. Sponsors committing to Rubin-Ultra-ready shells in 2026 are making a 5-year infrastructure bet — worth watching which sponsors step forward.

6. **AMD MI350X/MI400 traction.** If MI400 at 432GB HBM4 ships to hyperscaler anchors (Meta, Microsoft, Oracle continue to show interest), AMD's structural share gain becomes material — pricing pressure on equivalent-tier NVIDIA.

7. **Hyperscaler capex commentary.** Quarterly earnings calls from Microsoft, Google, Meta, AWS discussing GPU useful-life assumptions, capex intensity, and Trainium/Maia/TPU vs NVIDIA mix. These set baseline assumptions for the merchant GPU-operator environment.

8. **GPU-as-a-service private-credit structures.** First publicly disclosed senior-debt or term-loan B on GPU-collateralized assets at scale. Pricing benchmark.

9. **Export-control changes.** China-specific H20 already export-controlled; any expansion to H100 or B200 broad export restrictions would restructure secondary-market supply.

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
