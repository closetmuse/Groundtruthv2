DEEP DIVE — NSCALE'S MONARCH: THE BTU-TO-GPU VALUE CHAIN AND THE ALPHA BEING GENERATED
Flagged from AM brief 2026-04-24 0606ET  |  Source: GS-1912 RBN Energy 56.2 AMBER — "(They've Got) The Power — Nscale's Monarch Data Center Aims to Optimize the Btu-to-GPU Value Chain"
Written 2026-04-24 11:30 ET  |  Deep dive, not addendum — thematic analysis of a vertically-integrated AI-compute alpha thesis

================================================================
WHAT RBN REPORTED
================================================================

RBN's piece profiles **Nscale's Monarch Compute Campus**, under development in West Virginia (Marcellus/Appalachian gas country), framing the project as a **"Btu-to-GPU value chain"** — a vertically integrated stack where the same sponsor controls, or contracts on aligned terms, every layer from wellhead gas through to GPU-hour compute revenue. The RBN framing is analytical rather than transactional — a case study of a business model that is emerging as a distinct category inside the DC-build-out cycle, not a single deal announcement.

**Nscale background (for context):** UK-based AI cloud operator, originally spun out of Arkon Energy (Bitcoin-mining infrastructure) and pivoted to AI-compute in 2024. Has built or announced capacity at Glomfjord (Norway — stranded hydro), the UK (Microsoft partnership), and now Monarch (Appalachia). The financing has scaled — a ~$1.3bn raise during 2025 at roughly $3bn valuation, followed by hyperscaler anchoring commitments on the UK side. The company's stated positioning is "vertically integrated AI factory" — a phrase that is marketing but also technically accurate about the stack they are assembling.

The signal scored 56.2 AMBER — mid-tier weighting — but **the substance is structurally heavier than the score reflects.** What RBN's framing surfaces is a specific alpha mechanism that cuts across the LNG, Power, and DC axes simultaneously and contests the standard assumption that DC developers are power-takers.

================================================================
WHY THIS NOW
================================================================

Four structural conditions converged over 2024-26 to make vertically integrated BTU-to-GPU stacks economically compelling, and Nscale is the first scaled pure-play pursuing the full integration on US soil:

1. **Grid-interconnection as binding constraint.** Tier-1 DC markets (NoVa, Dallas, Phoenix, Silicon Valley, Chicago) have queue waits of 3-7 years for large-load interconnection. ERCOT, PJM, Dominion, and CAISO have all publicly flagged that forecast DC load is exceeding planned transmission build. For a developer racing to place 300-600 MW of AI training capacity inside an 18-24 month window, waiting four years for interconnection is commercially impossible. **Grid bypass becomes the only path.**

2. **Natgas basis dispersion at production hubs.** Appalachian basis (Marcellus/Utica pricing nodes — Dominion South, Leidy, TETCO M2) has traded $0.70-1.50/MMBtu below Henry Hub consistently through 2024-26 because pipeline takeaway capacity binds (Mountain Valley completion helped but did not close the basis gap). Waha basis (Permian) trades $1-3/MMBtu below HH for the same reason. A DC captive CCGT at a Marcellus site is seeing ~$1.50-2.00/MMBtu delivered gas vs a traditional DC paying $3-4/MMBtu delivered to Loudoun County. **Fuel cost differential of $1.50-2.00/MMBtu translates to $10-14/MWh generation cost advantage.**

3. **BTM (behind-the-meter) regulatory window opening.** The Trump-era FERC and DOE posture has softened on BTM large-load configurations. The Amazon-Talen PJM nuclear-DC BTM case (initially rejected Nov 2024, with partial subsequent relief) established the precedent that BTM DC is not categorically blocked. **Gas-fired BTM DC avoids the retail-cross-subsidization concerns that the nuclear-BTM fight raised** — the gas unit is a new-build behind the meter, not a reallocation of existing grid-ratepayer-supported capacity.

4. **GPU-cluster economics rewarding single-site scale.** Training-cluster power density has moved from ~10 kW/rack (2018-era) through 50-100 kW/rack (Blackwell era) and is heading toward 120-150 kW/rack with liquid cooling and NVLink domain expansion. Single-site 100-500+ MW AI training clusters are now standard. **A single-site multi-100-MW captive gas build is architecturally cleaner than threading that same load through a substation to grid** — and the gas-turbine buyer (Nscale-class operator) gets the GE Vernova-backlog pricing rather than the through-utility pass-through.

Nscale Monarch is the **first publicly-named pure-play AI operator** pursuing the fully-integrated Appalachian BTU-to-GPU stack at meaningful scale. Crusoe established the proving ground in the Permian on BTC-to-AI-pivot capital; Nscale is the Appalachian corollary with a different gas-basis profile and a different hyperscaler relationship structure. RBN's piece is recognition that this is now a category, not an outlier.

================================================================
MECHANISM — WHAT ALPHA IS NSCALE ACTUALLY GENERATING?
================================================================

The standard DC developer's P&L is a sequence of pass-throughs:
- Buys power at grid tariff ($60-90/MWh fully loaded in tier-1 markets).
- Buys rack/hall from colo operator at $140-200/kW-month delivered.
- Assembles GPU stack from cash (or GPU-as-a-service provider).
- Sells compute at market rate minus margin.

Each layer earns 15-25% gross margin. The developer is a power-taker at layer 1, a rack-taker at layer 2, and a price-taker on GPU procurement at layer 3. **Cumulative margin capture ~20-30% of end-revenue.**

The Nscale-Monarch vertically integrated model collapses the stack:

**Layer 1 — Feedstock arbitrage (gas).** Nscale (or its gas-supply counterparty under a long-term contract) sources Appalachian-basis gas at $1.50-2.00/MMBtu all-in at plant gate. Henry Hub is $2.71. A traditional DC in NoVa pays ~$3.50-4.00/MMBtu delivered gas-fired power; a Marcellus-sited DC pays ~$1.50-2.00/MMBtu. Differential: **$1.50-2.00/MMBtu, or ~40-50% off the national fuel benchmark.** Capitalized over a 15-year gas supply contract, this is $50-80/kW present value of fuel savings vs grid-tariff power, before any power-conversion efficiency effect.

**Layer 2 — Power conversion (CCGT).** Nscale-class builds typically deploy modern H-class or F-class CCGT in the 200-400 MW range, sized to campus load. Modern H-class runs 6,200-6,400 BTU/kWh heat rate (53-55% efficient); F-class 6,800-7,200. At the H-class/low-basis combination, marginal power cost comes out at roughly:

```
6,300 BTU/kWh × $1.75/MMBtu × (1/1000) = $11.0/MWh fuel
+ VOM $3-5/MWh = $14-16/MWh all-in variable generation cost
```

Compare to tier-1 grid power at $60-90/MWh all-in including demand charges: **Nscale's variable generation cost is 20-25% of grid-power cost.** Even amortizing the captive CCGT capex ($750-950/kW installed in current gas-turbine-backlog-constrained market) at 15-year project-finance senior debt and equity return, full-cost of power at the Monarch campus should clear at $35-50/MWh on a project-finance basis — still 40-50% below grid-tariff.

**Layer 3 — DC shell integration.** Conventional DC developers lease from colo operators (Digital Realty, Equinix, QTS, Stack) at $140-200/kW-month or negotiate build-to-suit at ~$12-16m/MW capex. Nscale-controlled shell means the shell capex goes into the vertically integrated P&L rather than becoming a rent pass-through. **Margin expansion of $40-60/kW-month vs pure-colo-tenant model.**

**Layer 4 — GPU cluster operation.** H100/H200/B200 clusters generate compute revenue at spot-market rates (currently Vast.ai p50 $1.56/hr H100; see GPU deep dive companion piece for details). An 8xH100 server at 90% utilization generates ~$110k revenue/year. The marginal cost breakdown — power (~$15-20k at $0.03-0.04/kWh captive), depreciation ($35-45k on $300k capex over 5-6yr), network, staff — leaves typical merchant GPU operators at 15-25% EBITDA margin. **Captive-power reduces the power line from $60-80k/year (grid) to $15-20k/year (captive) — EBITDA margin expands to 35-50% on the same revenue line.**

**Layer 5 — Hyperscaler anchor (the Microsoft / equivalent layer).** Nscale's playbook (UK-side already disclosed at ~$3bn GPU-as-a-service take-or-pay deal with Microsoft) suggests Monarch is being sized for a similar anchor structure. An anchored offtake means the DC-shell and CCGT are not merchant — they are anchored-project-finance-grade credit, and the financing structure shifts from merchant-DC speculative-build economics to anchored IG-capital-pool economics.

**Cumulative alpha being captured.** If each layer's margin delta is stacked:
- Fuel arbitrage: +$25-35/MWh vs grid-tariff peer.
- Power-conversion efficiency vs taker: +$15-25/MWh (captive CCGT heat rate + VOM discipline).
- DC-shell vertical integration: +$40-60/kW-month rent margin saved.
- GPU cluster run-cost reduction: +15-25 percentage points EBITDA margin.
- Hyperscaler anchor: senior-debt pricing tightens 150-300 bps, equity IRR hurdle drops 200-400 bps.

**The integrated cost-to-compute at a Monarch-class build is plausibly 40-55% below a tier-1-market merchant peer. That is the alpha.** On a GPU-hour pricing basis, if merchant peers clear at $1.50-2.00/GPU-hour breakeven, Nscale-class can clear at $0.70-1.10/GPU-hour breakeven. In a market where the spot-clearing rate is volatile and is set by the marginal merchant operator's breakeven, **Nscale's breakeven floor is structurally below the market-clearing level for merchant peers. They make money while merchant peers are at breakeven.**

================================================================
TIMELINE
================================================================

- **Monarch site preparation and permitting (2024-26):** West Virginia has historically permitted large gas-fired generation within 9-15 months. Air permits, gas lateral interconnect, and local siting are the binding path. Site grading and civil work proceeds in parallel.
- **CCGT order and delivery (2025-28):** GE Vernova's gas-turbine backlog is now 100 GW (per GS-1815 Thu PM capture). For new-order units, delivery is 36-48 months — meaning orders placed in 2025 arrive 2028-29. Nscale almost certainly had to either (a) take a slot that was already in the queue from a prior cancellation, (b) acquire existing CCGT-ready equipment on secondary market, or (c) accept a 2028+ COD for the full thermal buildout and commission GPU clusters first on partial-load or temporary power.
- **GPU cluster commissioning (2026-28):** Depends on hyperscaler anchor schedule. If Monarch is Microsoft-anchored on a similar pattern to UK, expect first Blackwell/B200 delivery 2026Q4-2027Q2, Rubin-class 2027+.
- **Hyperscaler offtake structured (2026-27):** The "Btu-to-GPU" narrative works because the hyperscaler contracts for GPU-hours, not for MW. Nscale captures the MW-to-GPU-hour margin. Structure-level disclosure is likely a take-or-pay commitment on a rolling cluster basis.
- **Alpha-durability window (2026-30):** The arbitrage persists as long as (a) grid-interconnect queues remain binding, (b) Appalachian basis holds at $0.70+/MMBtu below HH, (c) BTM regulatory window stays open, (d) GPU-hour pricing holds above $0.70-1.00 marginal. Any of the four weakening compresses the alpha.
- **Reversion catalysts (2028-32):** Grid buildout catches up; Appalachian basis closes as LNG export demand pulls gas to Gulf Coast; FERC revisits BTM doctrine under a different administration; GPU-hour pricing commoditizes into the $0.40-0.70 range.

================================================================
ASSET SPECIFICITY — WHO ELSE IS PLAYING THIS GAME
================================================================

Nscale-Monarch is a category, not an isolated deal. Category participants fit into several distinct credit profiles:

**Pure-play integrated AI-compute operators (Nscale tier).** Crusoe (Permian), Nscale (Appalachia + UK + Norway), Lambda (multi-geography), CoreWeave (mixed — started as Ethereum miner, now hyperscaler-anchored at traditional sites), Applied Digital (North Dakota, Texas). Each has a different geography-and-gas-profile combination. Crusoe and Nscale are the clearest vertically integrated examples. Financing profile: equity-heavy early, senior-debt thin, hyperscaler-anchored offtake is the credit-enhancement of choice.

**Hyperscaler-captive equivalents.** Microsoft's Abilene-class captive builds, Meta's Richland Parish and Louisiana builds, AWS captive capacity across multiple geographies, Google's Memphis and South Carolina builds. These are not "generating alpha" — they are internal build programs at hyperscaler cost-of-capital. They compete with Nscale for gas-turbine slots, for Appalachian or Haynesville siting, for labor. **Gas-turbine-backlog-constrained market means hyperscaler-captive and Nscale-class compete for the same scarce equipment.**

**Merchant-power developers who added DC-tenant thesis.** Vistra, Constellation, Talen, NRG: all currently valued at 20-35x earnings on the back of hyperscaler-anchored PPA narratives. Their business model is not vertically integrated — they own generation, sell power to DC tenant, DC-tenant is separate corporate entity. **Nscale-class directly disintermediates this model** when the integrated operator owns its own gas turbine.

**Upstream gas producers with DC-relevant basins.** EQT (Appalachia — most relevant to Monarch), Range Resources, Antero, CNX, Coterra, Chesapeake (now Expand Energy) — all have long-dated gas supply that could anchor a BTU-to-GPU partnership. **EQT's 2024-25 strategy statements explicitly flag DC-load-driven gas demand as a commercial priority.** Expect direct equity or long-term supply partnerships between Appalachian producers and Nscale-class operators to crystallize 2026-27.

**Midstream gas — the enabling infrastructure.** Short lateral pipes from producing fields to DC campuses are small capex items but continuous fee generators. Williams, Energy Transfer, Kinder Morgan, MPLX, EQT Midstream: incremental throughput without headline capex. Less alpha concentration, more breadth.

**GPU-infrastructure financiers.** GPU financing is emerging as a distinct asset class (see DC Axis 5 and the GPU deep dive companion). A Nscale-class vertically integrated operator can potentially carry larger GPU inventory on its balance sheet because the power-cost floor is structurally lower — higher GPU-utilization breakeven means less sensitivity to spot-market GPU-hour volatility.

================================================================
US PROJECT-FINANCE IMPLICATIONS — THE SRI DOMAIN SECTION
================================================================

This section addresses the specific deal-class and financing-structure implications for the US project-finance book.

**CCGT project finance at BTU-to-GPU sites.** The CCGT senior-debt structure is familiar — 15-20 year tenor, DSCR 1.25-1.40x sized, gas-supply contract and power-offtake contract as the two critical counterparty-credit legs. **The atypical feature is that the off-take is a DC operator, not a utility or merchant market.** Credit diligence must price:
- DC-operator credit as off-taker (Nscale is not rated; hyperscaler sub-anchor is the credit story).
- Gas-supply counterparty credit (Appalachian producer of EQT/Antero class — BB/BBB- area).
- Transmission and interconnection risk on the limited grid-tie for balancing / backup.
- Technology risk on the CCGT OEM (GE, Siemens, Mitsubishi — all investment-grade).
- **Concentration risk** — a single-site CCGT dependent on a single DC off-taker has concentration characteristics closer to merchant-DC than utility-scale power.

**Senior-debt pricing expectation.** Anchored-DC off-take with hyperscaler sub-anchor: **SOFR + 250-325bps, similar to pipeline-class anchored-DC senior debt.** Pure Nscale-credit off-take without hyperscaler anchor: **SOFR + 400-500bps, wrap-eligible.** Merchant-class would be SOFR + 600+ with ILS wrap or similar credit enhancement — this is where ALF-19-1 directly intersects.

**DC shell project finance at BTU-to-GPU sites.** DC shell at a Monarch-class site has the unusual property that the primary off-taker is the same corporate group that owns the underlying power asset. **This is a structural consolidation that most project-finance senior-debt structures haven't faced before.** Questions that arise:
- Can the DC senior debt and the CCGT senior debt cross-collateralize, or must they stand separately?
- If the integrated operator is distressed, does the DC lender have recourse to the CCGT separately, or is the whole stack a single enterprise?
- If a hyperscaler anchor lease on the DC side is triggered, does the CCGT revenue flow dependably?

**Deal-pattern implications.** Expect the first wave of Nscale-class financings to use a **hold-co equity / two-silo senior-debt structure** — DC senior debt at the shell SPV, CCGT senior debt at the power SPV, and unified hyperscaler offtake that revenue-feeds both. As the pattern matures, expect convergence toward **single-SPV integrated financing** with the CCGT and DC shell held together under a single senior-debt tranche, priced at the blended credit. The ILS-wrap structure ALF-19-1 tracks would fit the merchant-class version of this.

**For the current pipeline book.** The 44-deal book contains examples of:
- Tier-1-hyperscaler-anchored DC at traditional sites (senior debt conventional).
- Merchant-class DC at traditional sites (senior debt wider, wrap candidate).
- CCGT or gas-fired power at non-DC-anchored sites (conventional PF).

**Not yet in the book (and this is the point):** **Integrated BTU-to-GPU structure at a single site with same-entity cross-ownership of gas-lateral, CCGT, DC shell, and GPU cluster.** The Monarch-class structure is a template the book has not yet seen at scale. When the first such deal arrives for consideration — within 12-24 months, likely from a sponsor outside the current book — the underwriting framework will have to be built mostly from scratch. **The time to begin that template build is now, not when the first term sheet arrives.**

**Hedging and basis-risk considerations.** Nscale-class operators have natural long-gas-short-compute exposure over time. If Appalachian basis widens (compute-favorable) or Henry Hub spikes (compute-unfavorable — grid peers benefit less but still feel it), the integrated operator must decide whether to hedge or run the natural exposure. For senior-debt analysis, the question is whether the operator has a gas-price-hedge in place for the DSCR-measurement period.

**Cross-sector rate-of-change.** The speed with which this category is forming exceeds historical DC-developer-formation rates by 2-3x. Five years ago this structure would have been a whiteboard case. Today there are at least five scaled operators pursuing variants. **The ALF-19-1 substrate-maturation cadence observation from the 2026-04-24 AM brief reflects this same structural acceleration** — capital markets are responding to a category that is being formed at unusual speed.

================================================================
CROSS-AXIS THREADING
================================================================

**LNG Axis 1 (HH-JKM arb).** Appalachian basis widening (DC-pull keeping Marcellus gas in the basin) is slightly negative for Gulf Coast LNG feedstock economics — more DC-captive demand, less available for Sabine Pass / Corpus etc. Not sector-defining but material for long-dated LNG feedgas cost.

**LNG Axis 3 (Waha basis).** The Permian parallel to the Appalachian-Monarch story is Crusoe-class sites on Waha gas. Both basins experience similar BTU-to-GPU demand pull; both basis differentials compress modestly under sustained DC-captive demand.

**Power Axis 3 (Interconnection / FERC).** BTU-to-GPU BTM siting is the structural response to the queue-constraint problem Power Axis 3 tracks. The wider Nscale-class deploys, the less new-DC demand actually hits RTO interconnection queues. **Partial solution for the interconnect-queue problem, not full.** Power-sector transmission planners should update forecasts downward on this vector by ~10-20% of nominal new-DC demand over 2027-30.

**Power Axis 4 (curtailment / cost-to-system).** Nscale-class BTM sites are not curtailment-exposed — they do not sell power back to grid, they consume everything they generate. The Power Axis 4 mechanism (CAISO/ERCOT negative LMPs from over-building renewables) does not apply to integrated thermal-BTM DC. **Power-Axis-4-based LCOE-marginalization arguments do not extend to these operators.**

**DC Axis 1 (hyperscaler-DC durability).** Nscale-class operators are hyperscaler-compatible, not hyperscaler-substituting. The Microsoft UK deal is the template. DC Axis 1 durability thesis is reinforced, not challenged — hyperscaler commitment to the Nscale stack is part of the same durable-capex narrative.

**DC Axis 3 (supply-chain constraints).** BTU-to-GPU operators compete with hyperscalers for CCGT-turbine slots in the GE Vernova 100 GW backlog. This is a real binding-constraint transmission between DC Axis 3 and Power-upstream supply chain.

**DC Axis 5 (GPU financing).** BTU-to-GPU operators have structurally lower GPU-operating-cost floor, meaning GPU financing tenor and advance rate can be more aggressive against their stack. GPU financing at Nscale-class sites could price 100-200bps inside merchant-GPU-operator financing.

**DC Axis 6 (behind-the-meter).** Nscale-Monarch is the archetype BTM DC. The BTM regulatory window and its persistence is the foundation of the alpha.

**DC Axis 7 (ILS-wrapped DC senior debt).** The merchant-class variant of BTU-to-GPU (not hyperscaler-anchored) is a clear candidate consumer of ALF-19-1's ILS-wrap structure. Substrate advancement continues.

**ALF-20260420-W2 (DC hyperscaler-stack bifurcation candidate).** Nscale-class operators sit in the "hyperscaler-adjacent-but-independent" category — they benefit from hyperscaler offtake without being the hyperscaler captive. Strengthens the W2 bifurcation narrative: **three credit categories emerging, not two** — hyperscaler-captive (tier 1), hyperscaler-anchored independent integrated (Nscale class), merchant (tier 3).

================================================================
WHAT TO WATCH NEXT 30-90 DAYS
================================================================

1. **Monarch hyperscaler anchor disclosure.** If Nscale publicly names a hyperscaler anchor for Monarch (similar to the Microsoft UK structure), that is the trigger that moves the Monarch deal from announcement-stage to financeable. Absence of disclosure past Q3 2026 would be a negative signal.

2. **CCGT OEM announcement for Monarch.** Who is supplying the gas turbines? GE Vernova would be the base case; Mitsubishi or Siemens would indicate a secondary-market slot. The OEM choice tells us the deal's position in the 100 GW backlog queue.

3. **Appalachian gas-supply partner disclosure.** EQT, Antero, Range, or Expand Energy named as supply anchor to Monarch would validate the upstream-producer partnership pattern. This is the channel through which Marcellus-basis discount gets contractually locked.

4. **Senior debt or first-mortgage bond on the CCGT.** First project-financed Nscale-class CCGT on a US site. If it prints, the pricing and structure becomes the benchmark for the category. If it clears at SOFR + 275-325bps with hyperscaler anchor, the merchant-variant wrap-eligible spread target becomes ~SOFR + 500-600 — sizing the wrap-value-add at 150-275bps, which is material.

5. **Crusoe or CoreWeave Appalachian or Permian analog announcement.** Second scaled Nscale-class deal in the US would confirm the category; absence by Q3 2026 would suggest Nscale-Monarch is a one-off in the current cycle.

6. **FERC BTM doctrine stability.** Any regulatory statement or order that narrows BTM permissibility directly damages the category thesis. The Amazon-Talen saga continues to be the doctrinal test case — any new filings or orders are monitored.

7. **ERCOT, PJM, or MISO large-load interconnection process reform.** If an RTO materially shortens interconnection queues (unlikely but possible under certain reform packages), the alpha window narrows on the grid-constraint side.

8. **Hyperscaler balance-sheet posture on GPU-as-a-service procurement.** If Microsoft, Google, Meta, or AWS explicitly shift from owning-captive to leasing-from-Nscale-class operators as primary strategy, the category financialization accelerates. If instead hyperscalers double down on captive builds, the category stays mid-scale.

================================================================
ALPHA-LEDGER POSITIONING
================================================================

**No new ALF opened.** This deep dive does not contain a falsifiable time-bound market-price prediction with a defined verification latency — it is a structural category analysis, not an Alpha-ledger finding per the structural-alpha-framework discipline.

**Substrate accumulation toward existing and candidate ALFs:**

- **ALF-20260419-1 (ILS-wrapped DC senior debt IG uplift):** BTU-to-GPU merchant variant is a direct consumer of the ILS-wrap structure. Substrate note: the category growth directly enlarges the addressable market for the ALF-19-1 mechanism over 2027-30. The merchant-class Nscale-analog is the specific archetype consumer.

- **Candidate ALF-20260420-W2 (DC hyperscaler-stack bifurcation):** Nscale-class is a **third category** in the hyperscaler-credit-gradient (between hyperscaler-captive and pure-merchant). W2's bifurcation narrative may need to be refined to a **trifurcation** thesis: hyperscaler-captive (tier 1, prime credit) / hyperscaler-anchored-integrated (Nscale tier, near-IG with anchor) / merchant (wrap-eligible or spread-wide). This refinement is queued for Sunday weekly review.

- **Candidate forward-ALF (not opened today).** A future time-bound finding could be: "within 12 months of Monarch's CCGT senior-debt pricing, a second Nscale-class project finance will clear inside 50bps of that benchmark." That is a falsifiable structural prediction about category-financing convergence. **Do not open today** — waiting for Monarch's own senior-debt pricing to establish the reference point.

- **Forward-framing for LNG structural alpha.** Appalachian basis being held captive by DC-captive demand is a slow-burn positive for long-dated Gulf Coast LNG feedgas pricing. If material DC-gas-pull develops in Appalachia, feedgas basis for Gulf Coast LNG deteriorates modestly — a contract-structure positive for destination-prices-rising variants of the HH-JKM arb ALFs. Not today's ALF, but monitored.

================================================================

**TAPE TONE for the deep dive: integrated stack, captive margin, three-category market.**

================================================================
