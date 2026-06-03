# Domain knowledge: USSGL, TAFS, fund conventions

> **Status:** OSINT-sourced + synthetic. Real crosswalks/charts are open
> questions (Q-REF-1, Q-REF-2, Q-REF-3 in `docs/va-fmbt-open-questions.md`).

## USSGL (United States Standard General Ledger)

The Federal Accounting Standards Advisory Board (FASAB) and the US Treasury
mandate USSGL for executive-branch agencies. VA's FMBT must map every posting to
a 6-digit USSGL account. Key accounts relevant to VA financials:

| Account | Title | Common use at VA |
| --- | --- | --- |
| 101000 | Fund Balance with Treasury (FBWT) | Drawdowns for disbursements. |
| 131000 | Accounts Receivable | Revenue-side collections. |
| 211000 | Accounts Payable | Vendor obligations. |
| 310000 | Unexpended Appropriations – Cumulative | Obligation/expenditure headroom. |
| 480100 | Undelivered Orders – Obligations, Unpaid | Open obligations. |
| 490100 | Delivered Orders – Obligations, Unpaid | Goods/services received, not yet paid. |
| 610000 | Operating Expenses / Program Costs | Disbursed costs. |

The GL reference slice uses these accounts as a synthetic whitelist
(`mapper.py:USSGL_WHITELIST`). **Production requires** the fiscal-year USSGL chart
as configured in the Momentum instance.

## TAFS (Treasury Account Fund Symbol)

TAFS identifies the appropriation: agency code + period of availability + main
account + sub-account. The pattern for VA is:

```
036-YYYY/YYYY-XXXX-SSS
  |    |    |    |   |
  |    |    |    |   sub-account (000 = main)
  |    |    |    main account (fund code)
  |    |    end of period of availability
  |    beginning of period of availability
  agency (036 = VA)
```

The reference slice uses shortened TAFS (17-char) in the 20-byte treasury-symbol
field. Real format may differ.

## Fund codes (VA)

| Legacy code | Momentum fund | Description (reconstructed) |
| --- | --- | --- |
| 0160 | 0160-OPS | VA general operating (VHA) |
| 0162 | 0162-MEDSVC | Medical Services |
| 4537 | 4537-SCF | Supply Chain Fund (revolving) |
| 0152 | 0152-CONST | Construction appropriation |

This is a 4-entry synthetic crosswalk (`mapper.py:FUND_CROSSWALK`). Production
needs the full mapping including VBA/NCA/VACO appropriations and any sub-fund
detail.

## Budget object class (OMB A-11)

VA journals carry a 4-digit budget object class (OMB Circular A-11, §83).
Examples: `2520` (medical supplies), `2530` (non-medical supplies), `1100`
(personnel compensation). The factory validates format (4-char alphanumeric) but
cannot validate against Momentum's master data without Q-REF-3.
