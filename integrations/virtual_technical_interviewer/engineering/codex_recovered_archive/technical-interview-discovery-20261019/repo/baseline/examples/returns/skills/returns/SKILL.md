---
name: returns-triage
description: Apply a bounded fictional return-classification policy from three inputs.
---
Inputs: `condition ∈ {sealed, opened, damaged}`, `proof ∈ {yes,no}`, `days ∈ [0,365]`. Evaluation order: no proof→MANUAL_REVIEW; opened/damaged→INSPECT; sealed and age<=30→STANDARD_RETURN; else OUT_OF_WINDOW. Never issue a refund or write to external systems.
