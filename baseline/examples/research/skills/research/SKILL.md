---
name: research-diagnostics
description: Verify simple gross proxy margin using supplied numeric values and report clearly.
---
Inputs: revenue > 0 and cost >= 0, both in the same user-defined units/time period. Output `profit = revenue - cost` and `margin_percent = profit/revenue*100`, rounded only for display. Reject division by zero or invalid strings. Treat all numbers as user inputs, not independently verified business data.
