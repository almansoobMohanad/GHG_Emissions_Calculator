# GHG Emissions Dashboard Redesign Plan

## 🎯 Executive Summary

The new dashboard will transform from a simple data display to a **strategic emissions management tool** that reflects real-world GHG tracking practices, including:

1. **Baseline Year Concept** - Companies set their reference year for comparisons
2. **Scope Evolution Tracking** - Show how each scope's data coverage improves over time
3. **Year-over-Year Comparisons** - Only meaningful after baseline is established
4. **Scope-Specific Deep Dives** - Detailed breakdown for each scope across years

---

## 📋 Key Concepts to Implement

### 1. Baseline Year System
**What it is:**
- The year a company designates as their "complete" emissions inventory
- Usually after 1-3 years of tracking and improving data collection
- All future comparisons are made against this baseline

**Why it's important:**
- Early years show INCREASES as companies discover more emission sources
- This is normal and expected, not a failure
- Baseline year = when the company says "this is our true footprint"
- After baseline, reductions are meaningful

**Database Addition Needed:**
```sql
-- Add baseline_year to companies table
ALTER TABLE companies 
ADD COLUMN baseline_year INT DEFAULT NULL,
ADD COLUMN baseline_notes TEXT DEFAULT NULL;
```

---

## 🏗️ New Dashboard Structure

### **SECTION 1: Header & Context** (Top of page)
```
┌─────────────────────────────────────────────────────────┐
│ 🏠 Dashboard                                            │
│ Welcome back, [Username]! ([Role])                      │
│                                                         │
│ Company: [Company Name] ✅ Verified                     │
│ Baseline Year: [2023] 📌 Set on [Date]                 │
│ Current Tracking Year: [2026]                           │
└─────────────────────────────────────────────────────────┘
```

**Components:**
- User greeting with role
- Company info with verification badge
- **Baseline year indicator** (prominent display)
- Current year being tracked
- Button to set/change baseline year (Admin/Manager only)

---

### **SECTION 2: Year Selector & Mode Toggle**
```
┌─────────────────────────────────────────────────────────┐
│ 📅 Select Year: [Dropdown: 2021, 2022, 2023*, 2024...] │
│ 📊 View Mode: ○ Single Year  ● Multi-Year Comparison   │
└─────────────────────────────────────────────────────────┘
```

**Two View Modes:**

**Mode A: Single Year View**
- Shows detailed breakdown for one selected year
- All scopes, sources, categories
- Deep dive into that year's data

**Mode B: Multi-Year Comparison**
- Select multiple years (checkboxes or multi-select)
- Side-by-side comparison
- Only shows years AFTER baseline (with warning for pre-baseline)

---

### **SECTION 3: Baseline Status Panel** (New!)
```
┌─────────────────────────────────────────────────────────┐
│ 📌 Baseline Status                                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ IF NO BASELINE SET:                                     │
│   ⚠️ No baseline year set                              │
│   You are currently in the "Discovery Phase"           │
│   • Track emissions across all scopes                   │
│   • Improve data collection processes                   │
│   • When coverage is complete, set a baseline          │
│   [Set Baseline Year] button (Admin/Manager only)      │
│                                                         │
│ IF BASELINE SET:                                        │
│   ✅ Baseline Year: 2023                               │
│   Total Baseline Emissions: 1,245.67 tCO2e            │
│   Coverage: Scope 1 ✅ | Scope 2 ✅ | Scope 3 🟡       │
│   [View Baseline Details] [Change Baseline] buttons    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Clear indication of whether baseline is set
- If not set: Explanation + call to action
- If set: Quick stats + coverage indicators
- Admin controls to modify baseline

---

### **SECTION 4A: Single Year View** (When Mode A selected)

#### 4A.1 - Overview Cards
```
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Total        │ Scope 1      │ Scope 2      │ Scope 3      │
│ 1,234.56     │ 456.78       │ 123.45       │ 654.33       │
│ tCO2e        │ tCO2e        │ tCO2e        │ tCO2e        │
│              │              │              │              │
│ vs Baseline: │ vs Baseline: │ vs Baseline: │ vs Baseline: │
│ +12.5% 🔴    │ -5.2% 🟢     │ +2.1% 🔴     │ +18.9% 🔴    │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

**Features:**
- Big number metrics
- Each scope as separate card
- Comparison to baseline (if set)
- Color coding: Green (reduction), Red (increase), Gray (no baseline)
- If year is BEFORE baseline: Show "Pre-baseline year" instead of comparison

#### 4A.2 - Scope Breakdown Tabs
```
┌─────────────────────────────────────────────────────────┐
│ 📊 Scope Analysis                                       │
│ [Scope 1] [Scope 2] [Scope 3]                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Selected: Scope 1 - Direct Emissions                    │
│                                                         │
│ Total: 456.78 tCO2e                                     │
│ Number of Sources: 15                                   │
│ Coverage Status: ✅ Complete                           │
│                                                         │
│ ┌─────────────────────────────────────────────┐        │
│ │ Top Sources (Pie Chart or Bar Chart)        │        │
│ │ - Stationary Combustion: 320.45 tCO2e      │        │
│ │ - Mobile Combustion: 136.33 tCO2e          │        │
│ └─────────────────────────────────────────────┘        │
│                                                         │
│ ┌─────────────────────────────────────────────┐        │
│ │ Monthly/Quarterly Trend (Line Chart)         │        │
│ └─────────────────────────────────────────────┘        │
│                                                         │
│ [View Detailed Data] button                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Separate tab for each scope
- Summary stats for that scope
- Coverage indicator (Complete/Partial/Missing)
- Visual breakdown of sources within scope
- Temporal trend within the year
- Link to detailed data view

---

### **SECTION 4B: Multi-Year Comparison** (When Mode B selected)

#### 4B.1 - Year Selection
```
┌─────────────────────────────────────────────────────────┐
│ Select Years to Compare:                                │
│ ☐ 2021 (Pre-baseline)                                  │
│ ☐ 2022 (Pre-baseline)                                  │
│ ☑ 2023 (Baseline) 📌                                   │
│ ☑ 2024                                                  │
│ ☑ 2025                                                  │
│ ☑ 2026 (Current)                                        │
│                                                         │
│ ⚠️ Warning: Years before baseline (2021, 2022)         │
│    typically show increases due to improved tracking.   │
│    Comparison may not reflect actual emission changes.  │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Multi-select checkboxes for years
- Visual distinction for pre-baseline years
- Baseline year always highlighted
- Warning message if pre-baseline years selected

#### 4B.2 - Total Emissions Comparison
```
┌─────────────────────────────────────────────────────────┐
│ 📈 Total Emissions Trend                                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  (Line Chart or Bar Chart)                              │
│                                                         │
│  1,500 ┤                                    ╭──○ 2026   │
│  1,400 ┤                          ╭────○                │
│  1,300 ┤                    ○────╯                      │
│  1,200 ┤           ○────────╯     (Baseline: 2023)      │
│  1,100 ┤      ○────╯                                    │
│  1,000 ┤  ○───╯                                         │
│        └────────────────────────────────────────        │
│         2021 2022 2023 2024 2025 2026                  │
│                                                         │
│  📊 Change from Baseline:                               │
│  • 2024: +5.2% (+65.34 tCO2e) 🔴                       │
│  • 2025: +8.7% (+109.23 tCO2e) 🔴                      │
│  • 2026: +12.1% (+151.89 tCO2e) 🔴                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Line chart showing trend across selected years
- Baseline year marked with vertical line or annotation
- Table showing % change from baseline
- Color coding for increases/decreases

#### 4B.3 - Scope-by-Scope Comparison
```
┌─────────────────────────────────────────────────────────┐
│ 🔍 Scope-by-Scope Analysis                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  (Grouped Bar Chart - 3 bars per year for each scope)  │
│                                                         │
│  1,000 ┤                                                │
│   800  ┤     ███                                        │
│   600  ┤     ███  ███                                   │
│   400  ┤ ███ ███  ███  ███                             │
│   200  ┤ ███ ███  ███  ███                             │
│      0 ┴─────────────────────                          │
│         2023 2024 2025 2026                            │
│         ███ Scope 1  ███ Scope 2  ███ Scope 3         │
│                                                         │
│  Or Stacked Bar Chart:                                  │
│         Each bar = 1 year, segments = scopes           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Visual comparison of how each scope changed
- Option to toggle between grouped and stacked view
- Shows which scopes are driving overall changes

#### 4B.4 - Detailed Comparison Table
```
┌─────────────────────────────────────────────────────────┐
│ 📋 Detailed Year-over-Year Comparison                   │
├─────────┬──────────┬──────────┬──────────┬─────────────┤
│ Scope   │ 2023     │ 2024     │ 2025     │ 2026        │
│         │(Baseline)│          │          │             │
├─────────┼──────────┼──────────┼──────────┼─────────────┤
│ Scope 1 │ 456.78   │ 432.10   │ 445.23   │ 467.89      │
│         │          │ -5.4% 🟢 │ -2.5% 🟢 │ +2.4% 🔴    │
├─────────┼──────────┼──────────┼──────────┼─────────────┤
│ Scope 2 │ 123.45   │ 126.11   │ 130.45   │ 135.67      │
│         │          │ +2.2% 🔴 │ +5.7% 🔴 │ +9.9% 🔴    │
├─────────┼──────────┼──────────┼──────────┼─────────────┤
│ Scope 3 │ 654.33   │ 689.02   │ 723.11   │ 765.44      │
│         │          │ +5.3% 🔴 │ +10.5% 🔴│ +17.0% 🔴   │
├─────────┼──────────┼──────────┼──────────┼─────────────┤
│ TOTAL   │ 1,234.56 │ 1,247.23 │ 1,298.79 │ 1,369.00    │
│         │          │ +1.0% 🔴 │ +5.2% 🔴 │ +10.9% 🔴   │
└─────────┴──────────┴──────────┴──────────┴─────────────┘
```

**Features:**
- Tabular data for precise numbers
- Percentage changes from baseline
- Color coding
- Can be exported to CSV/Excel

---

### **SECTION 5: Coverage & Data Quality Indicators** (New!)
```
┌─────────────────────────────────────────────────────────┐
│ 📊 Data Coverage Evolution                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Shows how data collection improved over the years:      │
│                                                         │
│ Year  │ Scope 1 │ Scope 2 │ Scope 3 │ Overall          │
│ ──────┼─────────┼─────────┼─────────┼─────────         │
│ 2021  │  45%    │  80%    │  10%    │  🟡 Partial     │
│ 2022  │  78%    │  95%    │  35%    │  🟡 Improving   │
│ 2023* │  100%   │  100%   │  85%    │  ✅ Baseline    │
│ 2024  │  100%   │  100%   │  90%    │  ✅ Complete    │
│ 2025  │  100%   │  100%   │  95%    │  ✅ Complete    │
│ 2026  │  100%   │  100%   │  98%    │  ✅ Complete    │
│                                                         │
│ * = Baseline Year                                       │
│                                                         │
│ 💡 Insight: Scope 3 coverage improved significantly     │
│    from 10% (2021) to 98% (2026), explaining much      │
│    of the reported emission increase.                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**How to Calculate Coverage:**
- Manual input by user (simple approach)
- Or automatic: (number of sources tracked) / (expected sources) × 100
- Or by categories covered in each scope

---

### **SECTION 6: Insights & Recommendations** (New!)
```
┌─────────────────────────────────────────────────────────┐
│ 💡 Key Insights                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Based on your data from 2023 (baseline) to 2026:       │
│                                                         │
│ 🔴 Total emissions increased by 10.9%                   │
│                                                         │
│ 🟢 Scope 1 emissions decreased by 2.4% (Good!)         │
│    Main driver: Reduction in stationary combustion      │
│                                                         │
│ 🔴 Scope 2 emissions increased by 9.9%                  │
│    Main driver: Increased electricity consumption       │
│    💡 Consider: Renewable energy procurement            │
│                                                         │
│ 🔴 Scope 3 emissions increased by 17.0%                 │
│    Note: Coverage improved from 85% to 98%             │
│    Actual increase (adjusted for coverage): ~8%         │
│                                                         │
│ 🎯 Recommendations:                                     │
│    1. Focus on Scope 2: Explore green energy options   │
│    2. Continue improving Scope 3 data collection       │
│    3. Maintain Scope 1 reduction efforts               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- Auto-generated insights based on data
- Identifies which scopes are improving/worsening
- Contextualizes increases (e.g., due to better tracking)
- Actionable recommendations

---

### **SECTION 7: Quick Actions** (Existing, but reorganized)
```
┌─────────────────────────────────────────────────────────┐
│ 🎯 Quick Actions                                        │
├─────────────────────────────────────────────────────────┤
│ [➕ Add New Activity]                                   │
│ [📊 View Detailed Data]                                │
│ [📋 Generate Report]                                    │
│ [✅ Verify Data]                                        │
│ [⚙️ Set Baseline Year] (Admin only)                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🗄️ Database Changes Required

### 1. Companies Table - Add Baseline Year
```sql
ALTER TABLE companies 
ADD COLUMN baseline_year INT DEFAULT NULL,
ADD COLUMN baseline_notes TEXT DEFAULT NULL,
ADD COLUMN baseline_set_date DATE DEFAULT NULL,
ADD COLUMN baseline_set_by INT DEFAULT NULL,
ADD CONSTRAINT fk_baseline_set_by 
    FOREIGN KEY (baseline_set_by) REFERENCES users(id);
```

### 2. Optional: Coverage Tracking Table (for advanced features)
```sql
CREATE TABLE emissions_coverage (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    year INT NOT NULL,
    scope_number INT NOT NULL,
    coverage_percentage DECIMAL(5,2) DEFAULT NULL,
    total_expected_sources INT DEFAULT NULL,
    tracked_sources INT DEFAULT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(id),
    UNIQUE KEY unique_company_year_scope (company_id, year, scope_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 🎨 Visual Design Guidelines

### Color Scheme for Comparisons
- **Green (🟢)**: Reduction from baseline (good)
- **Red (🔴)**: Increase from baseline (needs attention)
- **Gray (⚪)**: No baseline set or pre-baseline data
- **Blue (🔵)**: Baseline year itself
- **Yellow (🟡)**: Warning/Partial data

### Icons & Badges
- 📌 Baseline year indicator
- ✅ Complete coverage
- 🟡 Partial coverage
- ❌ Missing data
- 🔴 Increase
- 🟢 Decrease
- ⚠️ Warning/Notice

---

## 📱 Responsive Layout

### Desktop (Wide Screen)
- Two-column layout for comparisons
- Side-by-side charts
- Full tables

### Tablet/Mobile
- Single column layout
- Stacked charts
- Collapsible sections
- Swipeable year comparison

---

## ⚙️ Technical Implementation Plan

### Phase 1: Foundation (Week 1)
1. Add baseline year to database
2. Create baseline year selector modal/dialog
3. Update company info display to show baseline
4. Add baseline year to session state

### Phase 2: Core Features (Week 2)
1. Implement view mode toggle (Single Year vs Multi-Year)
2. Build baseline status panel
3. Create year comparison logic
4. Add "vs baseline" calculations to all metrics

### Phase 3: Visualizations (Week 3)
1. Build scope breakdown tabs
2. Create multi-year comparison charts
3. Add scope-by-scope comparison views
4. Implement detailed comparison table

### Phase 4: Advanced Features (Week 4)
1. Coverage tracking system (optional)
2. Auto-generated insights
3. Recommendations engine
4. Export functionality for comparisons

### Phase 5: Polish & Testing (Week 5)
1. UI/UX refinements
2. Performance optimization
3. Testing with real data
4. Documentation

---

## 🧪 Testing Scenarios

### Test Case 1: New Company (No Baseline)
- Show "Discovery Phase" message
- All comparisons disabled
- Encourage setting baseline when ready

### Test Case 2: Company with Baseline Set
- Show baseline year prominently
- All comparisons reference baseline
- Multi-year comparisons enabled

### Test Case 3: Pre-Baseline Years Selected
- Show warning message
- Explain that increases are normal
- Still allow comparison but with context

### Test Case 4: Multiple Year Selection
- Charts update dynamically
- All selected years shown in comparison
- Baseline always highlighted

---

## 📊 Example User Journeys

### Journey 1: First-Time User (No Baseline)
1. Logs in → sees Dashboard
2. Sees "No baseline year set" with explanation
3. Understands they're in "Discovery Phase"
4. Adds emissions data for 1-2 years
5. Admin sets baseline when coverage is good
6. Dashboard transforms to show meaningful comparisons

### Journey 2: Established User (Baseline Set)
1. Logs in → sees Dashboard
2. Immediately sees "vs Baseline" metrics
3. Switches to Multi-Year Comparison mode
4. Selects 2023 (baseline), 2024, 2025, 2026
5. Views trend chart showing emissions trajectory
6. Drills down into Scope 2 to investigate increase
7. Generates report for management

### Journey 3: Annual Review
1. It's January 2027
2. All 2026 data is verified
3. User reviews 2026 vs baseline performance
4. Identifies Scope 3 as biggest increase
5. Checks coverage - it improved from 85% to 95%
6. Realizes "real" increase is smaller than reported
7. Sets reduction targets for 2027

---

## 🎯 Success Metrics

After implementation, the dashboard should enable users to:

1. ✅ Understand what baseline year means and why it matters
2. ✅ Clearly see if emissions are truly increasing or just coverage improving
3. ✅ Identify which scopes need the most attention
4. ✅ Track progress year-over-year in a meaningful way
5. ✅ Make data-driven decisions about reduction strategies
6. ✅ Generate insights for management and stakeholders

---

## 📚 Additional Features to Consider (Future)

1. **Target Setting**
   - Set reduction targets per scope
   - Track progress toward targets
   - Visual indicators (on track, at risk, off track)

2. **Scenario Planning**
   - "What if" calculator
   - Model impact of reduction initiatives
   - Compare different reduction strategies

3. **Benchmarking**
   - Compare with industry averages
   - Show percentile rankings
   - Best practice suggestions

4. **Forecasting**
   - Predict future emissions based on trends
   - Identify if on track to meet targets
   - Early warning system

5. **Certification Readiness**
   - Track requirements for ISO 14064, GHG Protocol, etc.
   - Gap analysis
   - Compliance checklist

---

## 🎓 Educational Elements

Add tooltips and help text explaining:
- What is a baseline year?
- Why emissions increase in early years
- How to interpret year-over-year changes
- What good coverage looks like for each scope
- Industry best practices for target setting

---

## 📝 Documentation Needs

1. **User Guide**: How to use the new dashboard
2. **Admin Guide**: How to set/change baseline year
3. **Best Practices**: When to set baseline, how to improve coverage
4. **FAQ**: Common questions about baseline year concept

---

## 🚀 Next Steps

1. **Review this plan** with supervisor for approval
2. **Prioritize features** - which are must-have vs nice-to-have
3. **Create mockups** - visual designs for approval
4. **Start with database changes** - foundation for everything else
5. **Implement incrementally** - one section at a time
6. **Get user feedback** - test early and often

---

**Questions for Supervisor:**

1. Is the baseline year concept correctly understood?
2. Should we track coverage manually or automatically?
3. Are there specific charts/visualizations they want to see?
4. Should we implement all features or start with core ones?
5. Any specific industry standards to follow (GHG Protocol, ISO, etc.)?
6. Should the dashboard be customizable by user role?

---

**End of Plan**
