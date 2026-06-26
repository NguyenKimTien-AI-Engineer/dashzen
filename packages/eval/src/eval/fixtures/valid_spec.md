---
name: Revenue Dashboard
language: en
version: 1
dataSource:
  type: csv
  file: sales.csv
refresh: static
---

# Purpose
Track revenue by region for executive decisions.

# Audience
Executive team

# Filters
| id | label | type | field | default |
|----|-------|------|-------|---------|
| date_range | Date range | dateRange | order_date | last_30_days |
| region | Region | select | region | all |

# Widgets

## total_revenue
- **type:** kpi
- **title:** Total Revenue
- **metric:** Sum of order amounts
- **field(s):** amount
- **aggregation:** sum
- **format:** currency
- **description:** Overall revenue KPI

## revenue_by_region
- **type:** barChart
- **title:** Revenue by Region
- **metric:** Revenue per region
- **field(s):** region, amount
- **aggregation:** sum
- **format:** currency
- **description:** Regional breakdown

# Metrics glossary
| metric_id | label | definition | source_field | aggregation |
|-----------|-------|------------|--------------|-------------|
| total_revenue | Total Revenue | Sum of order amounts | amount | sum |
| revenue_by_region | Revenue by Region | Revenue grouped by region | amount | sum |

# Empty states
Show "No data for selected filters" when filter returns zero rows.

# Notes
All metrics map to sales.csv columns.
