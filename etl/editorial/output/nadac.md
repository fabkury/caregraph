## Overview

NADAC (National Average Drug Acquisition Cost) is a Medicaid program administered by CMS that publishes the average price retail community pharmacies pay to acquire prescription drugs. The data is collected through a voluntary monthly survey of approximately 2,500 retail community pharmacies, conducted by Myers and Stauffer LC under contract with CMS. NADAC is updated weekly and represents the most transparent publicly available measure of actual drug acquisition costs in the United States.

NADAC reports per-unit ingredient costs at the NDC (National Drug Code) level, covering both brand-name and generic drugs dispensed in the retail community pharmacy channel. CareGraph uses the most recent available NADAC snapshot at the time of ETL. On drug entity pages, NADAC answers the question: what does a pharmacy typically pay to acquire this drug, before dispensing fees, markups, or rebates are applied?

## Join Strategy

NADAC records are matched to CareGraph drug entities by generic drug name. Each NADAC record includes an NDC and a drug name string; CareGraph normalizes the drug name and joins it to its canonical drug entities using the generic name. This join is performed as a string match after lowercasing and stripping salt-form suffixes where feasible.

Because NADAC reports at the NDC level â€” which distinguishes between strengths, dosage forms, and package sizes â€” multiple NADAC records may map to a single CareGraph drug entity. CareGraph aggregates or selects representative records per drug entity during ETL. The matched NADAC data appears on drug entity pages (e.g., `/drug/metformin`).

Name-based matching introduces ambiguity for combination products, extended-release formulations, and drugs with multiple salt forms (e.g., metoprolol tartrate vs. metoprolol succinate). These cases may result in imprecise matches or missed joins.

## Known Limitations

- **Medicaid channel only.** NADAC reflects acquisition costs for retail community pharmacies in the Medicaid supply chain. Prices in other channels â€” hospital, specialty pharmacy, mail-order, and 340B covered entities â€” may differ substantially and are not represented.
- **Voluntary survey with variable response rates.** The pharmacy survey is voluntary. For widely dispensed generics, survey response counts are robust. For specialty drugs or drugs with limited retail distribution, few pharmacies may report, producing less reliable cost estimates.
- **Ingredient cost only.** NADAC excludes dispensing fees, pharmacy markups, and manufacturer rebates. For branded drugs, the gap between NADAC and what payers actually pay net of rebates can be substantial, making NADAC a poor proxy for net drug cost.
- **Point-in-time snapshot.** CareGraph currently captures only the most recent NADAC price, not historical price trends. NADAC prices can fluctuate weekly, so the displayed price reflects a single point in time that may not represent longer-term pricing.
- **Drug name matching ambiguity.** Joining NADAC to CareGraph drug entities by generic name can produce imprecise matches for combination products, extended-release vs. immediate-release formulations, and drugs marketed under multiple salt forms.
- **No coverage of non-retail drugs.** Drugs primarily administered in clinical settings (physician-administered injectables, infusion drugs) may be absent or poorly represented in NADAC, since these are not typically dispensed through retail community pharmacies.

## Data Quality Notes

- **Multiple records per drug.** A single generic drug name may have dozens of NADAC records corresponding to different NDCs (strengths, dosage forms, manufacturers, package sizes). ETL must select or aggregate appropriately to avoid displaying misleading unit costs.
- **Drug name string inconsistencies.** NADAC drug name fields may include salt forms, dosage form abbreviations, or strength information in inconsistent formats (e.g., "HCL" vs. "HYDROCHLORIDE"), requiring normalization before join matching.
- **Unit price precision.** NADAC unit prices are reported to multiple decimal places and represent per-unit costs (per tablet, per mL, etc.). The unit basis varies by dosage form and is not always intuitive for end users without the corresponding unit-of-measure field.
- **Weekly update cadence vs. ETL cadence.** Because NADAC is updated weekly but CareGraph ETL runs manually, the displayed price may lag the current NADAC by days or weeks depending on when ETL was last executed.
