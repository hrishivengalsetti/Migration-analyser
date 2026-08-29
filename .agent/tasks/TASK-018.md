# TASK-018: Demo Projects Construction

**Milestone**: M10  
**Assigned to**: LatentCode  
**Status**: pending  
**Depends on**: TASK-012 (complete)  

---

## Goal

Create purpose-built `demo/original/` and `demo/migrated/` Python projects designed to produce a predictable, impressive demo result when submitted to the Migration Verifier. The original project is a small e-commerce pricing module with unit tests. The migrated version contains a refactored `calculate_discount()` function with an intentional off-by-one regression that breaks a unit test. Running these through the tool must deterministically produce `REGRESSION_DETECTED`.

---

## Context Files to Read

Before implementing:
1. `.agent/constitution.md`
2. `.agent/architecture.md`
3. `backend/models.py` — understand the data models that will be exercised
4. `backend/pipeline/runner.py` (from TASK-012)
5. This task file

---

## Inputs

- Working pipeline from TASK-012

## Outputs

```
demo/
├── original/
│   ├── ecommerce/
│   │   ├── __init__.py
│   │   ├── pricing.py          ← Core pricing logic
│   │   ├── checkout.py         ← Checkout workflow using pricing
│   │   └── tax.py              ← Tax calculation
│   └── tests/
│       ├── __init__.py
│       ├── test_pricing.py     ← Tests for pricing module
│       ├── test_checkout.py    ← Tests for checkout module
│       └── test_tax.py         ← Tests for tax module
├── migrated/
│   ├── ecommerce/
│   │   ├── __init__.py
│   │   ├── pricing.py          ← Refactored with intentional bug
│   │   ├── checkout.py         ← Same as original (calls pricing)
│   │   └── tax.py              ← Same as original
│   └── tests/
│       ├── __init__.py
│       ├── test_pricing.py     ← Same tests (one will fail)
│       ├── test_checkout.py    ← Same tests
│       └── test_tax.py         ← Same tests
└── README.md
```

---

## Acceptance Criteria

### AC-1: Original project — correct implementation
- `ecommerce/pricing.py` contains:
  - `calculate_discount(price: float, discount_percent: float) -> float`: returns `price * (1 - discount_percent / 100)`
  - `calculate_bulk_discount(price: float, quantity: int) -> float`: returns tiered discount (e.g., 10% for 10+, 20% for 50+)
- `ecommerce/tax.py` contains:
  - `apply_tax(price: float, tax_rate: float = 0.08) -> float`: returns `price * (1 + tax_rate)`
- `ecommerce/checkout.py` contains:
  - `checkout(items: list[dict]) -> dict`: processes a list of `{"name", "price", "quantity"}` dicts, applies discount and tax, returns order summary
  - `checkout()` imports and calls `calculate_discount()`, `calculate_bulk_discount()`, and `apply_tax()`

### AC-2: Original project — all tests pass
- `tests/test_pricing.py` contains at least 4 tests:
  - `test_no_discount` — 0% discount returns original price
  - `test_standard_discount` — 10% off $100 = $90
  - `test_bulk_discount_small_order` — quantity < 10 → no bulk discount
  - `test_bulk_discount_large_order` — quantity >= 10 → 10% discount applied
- `tests/test_checkout.py` contains at least 2 tests:
  - `test_single_item_checkout` — one item checkout returns correct total
  - `test_multi_item_checkout` — multiple items with bulk discount
- `tests/test_tax.py` contains at least 2 tests:
  - `test_default_tax_rate` — default 8% tax
  - `test_custom_tax_rate` — custom tax rate applied
- ALL tests pass when running `cd demo/original && python -m pytest tests/ -v`

### AC-3: Migrated project — intentional regression
- `ecommerce/pricing.py` in `migrated/` has a refactored `calculate_discount()`:
  - The function is "refactored" with different internal logic (e.g., using a different calculation approach)
  - Contains an intentional off-by-one bug: e.g., `price * (1 - (discount_percent + 1) / 100)` or similar subtle arithmetic error
  - The bug MUST cause `test_standard_discount` to fail (expected $90 but gets a different value)
- ALL OTHER files in `migrated/` are identical to `original/`
- The regression must be subtle and realistic — not an obviously fake error

### AC-4: Migrated project — some tests pass, one fails
- Running `cd demo/migrated && python -m pytest tests/ -v`:
  - `test_standard_discount` FAILS (because of the regression)
  - ALL other tests PASS

### AC-5: Pipeline produces REGRESSION_DETECTED
- Zipping `demo/original/` and `demo/migrated/` and submitting to the tool:
  - Classification must be `REGRESSION_DETECTED`
  - The evidence must show `calculate_discount` with `comparison="regression"`
  - The blast radius must include `checkout` (since it calls `calculate_discount`)

### AC-6: Import/call relationships exist
- The demo project has clear import/call chains:
  - `checkout.py` imports from `pricing.py` and `tax.py`
  - This ensures the blast radius graph has visible edges
  - This ensures the demo shows both changed symbols and affected symbols

### AC-7: README
- `demo/README.md` explains:
  - What the demo projects contain
  - What the intentional regression is
  - How to run the demo
  - Expected output

---

## Non-Goals

- Do NOT make the demo project complex — keep it small and focused
- Do NOT add third-party dependencies to the demo project
- Do NOT add configuration files beyond what pytest needs
- Do NOT add CI/CD configuration

---

## Technical Constraints

- Demo projects must work with Python 3.11
- Demo projects must only use Python stdlib (no external packages except pytest for tests)
- Demo tests must work with `pytest` (installed in the Docker test runner)
- Keep each file under 50 lines

---

## Verification

```bash
cd demo/original && python -m pytest tests/ -v
# ALL tests should pass

cd demo/migrated && python -m pytest tests/ -v
# test_standard_discount should FAIL, all others should PASS
```

---

## Blocker Section

*(LatentCode fills this in if blocked)*

---

## Implementation Plan

*(LatentCode fills this in before implementing)*
