# GHG Scopes and Categories Schema (GHG Protocol Aligned)

This schema is used by `scripts/setup_ghg_factors.py`.

## Scope-level schema

| Scope Number | Scope Name | Definition |
|---|---|---|
| 1 | Scope 1: Direct Emissions | Direct GHG emissions from sources owned or controlled by the organization. |
| 2 | Scope 2: Energy Indirect Emissions | Indirect emissions from purchased electricity, steam, heat, and cooling. |
| 3 | Scope 3: Other Indirect Emissions | All other indirect emissions across upstream and downstream value chain activities. |

## Category schema

### Scope 1 categories (internal operational breakdown)

| Category Code | Category Name | Description |
|---|---|---|
| S1-FUEL | Fuel Combustion | Emissions from stationary and mobile fuel combustion. |
| S1-FUGITIVE | Fugitive Emissions | Intentional or unintentional releases (e.g., refrigerants, SF6). |
| S1-PROCESS | Process Emissions | Emissions from industrial/process reactions. |

### Scope 2 categories (internal operational breakdown)

| Category Code | Category Name | Description |
|---|---|---|
| S2-ELECTRICITY | Purchased Electricity | Purchased electricity from grid/suppliers. |
| S2-HEAT-STEAM | Purchased Heat, Steam, and Cooling | Purchased district heat, steam, or cooling. |

### Scope 3 categories (GHG Protocol standard 15 categories)

| Category Code | GHG Protocol Category | Upstream/Downstream | Description |
|---|---|---|---|
| S3-01-GOODS | Category 1: Purchased Goods and Services | Upstream | Emissions from purchased goods/services (including water and purchased materials). |
| S3-02-CAPITAL | Category 2: Capital Goods | Upstream | Emissions from purchased capital goods. |
| S3-03-FUEL-ENERGY | Category 3: Fuel- and Energy-Related Activities (not in Scope 1 or 2) | Upstream | Well-to-tank and T&D losses not covered in Scope 1/2. |
| S3-04-UPSTREAM-TRANSPORT | Category 4: Upstream Transportation and Distribution | Upstream | Third-party transport/distribution of purchased goods. |
| S3-05-WASTE | Category 5: Waste Generated in Operations | Upstream | Treatment/disposal of operational waste. |
| S3-06-BUSINESS-TRAVEL | Category 6: Business Travel | Upstream | Employee business travel, including hotel stays. |
| S3-07-COMMUTING | Category 7: Employee Commuting | Upstream | Employee commuting and remote working impacts (if tracked). |
| S3-08-UPSTREAM-ASSETS | Category 8: Upstream Leased Assets | Upstream | Operation of leased assets not in Scope 1/2. |
| S3-09-DOWNSTREAM-TRANSPORT | Category 9: Downstream Transportation and Distribution | Downstream | Third-party transport/distribution of sold goods. |
| S3-10-PROCESSING | Category 10: Processing of Sold Products | Downstream | Processing by third parties of sold intermediate products. |
| S3-11-USE-PRODUCTS | Category 11: Use of Sold Products | Downstream | Product use-phase emissions. |
| S3-12-END-LIFE | Category 12: End-of-Life Treatment of Sold Products | Downstream | Waste treatment/disposal of sold products at end-of-life. |
| S3-13-DOWNSTREAM-ASSETS | Category 13: Downstream Leased Assets | Downstream | Operation of assets owned by reporting company and leased to others. |
| S3-14-FRANCHISES | Category 14: Franchises | Downstream | Emissions from franchise operations. |
| S3-15-INVESTMENTS | Category 15: Investments | Downstream | Emissions from investments and financed activities. |

## Category migration notes

- Removed custom category `S3-HOTEL`; hotel stay factors map to `S3-06-BUSINESS-TRAVEL`.
- Removed custom category `S3-MATERIALS`; material factors map to `S3-01-GOODS`.
- Freight factors are split between:
  - `S3-04-UPSTREAM-TRANSPORT` (upstream movement of purchased goods)
  - `S3-09-DOWNSTREAM-TRANSPORT` (downstream movement of sold products)
