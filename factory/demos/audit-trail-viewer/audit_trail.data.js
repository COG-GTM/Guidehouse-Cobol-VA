window.AUDIT_TRAIL = {
  "run_id": "run-gl-with_rejects-49a12f6419",
  "generated_at": "2026-06-08T16:22:55+00:00",
  "slice": "gl",
  "slice_title": "GL / journal extract",
  "source_copybook": "source/GL-JOURNAL-EXTRACT-REC.cpy",
  "target_contract": "MOMENTUM-JOURNAL-IMPORT",
  "fixture": "gl_extract_with_rejects.dat",
  "group_label": "journal",
  "summary": {
    "lines_in": 12,
    "loaded": 6,
    "rejected": 6,
    "row_accounting_ok": true,
    "legacy_control_total": "400000.00",
    "target_control_total": "400000.00",
    "control_total_ok": true,
    "mapping_coverage": 0.5,
    "reject_reasons": {
      "BAD_DATE": 1,
      "BAD_DR_CR": 1,
      "BAD_FUND": 1,
      "BAD_USSGL": 1,
      "NON_NUMERIC": 1,
      "ZERO_AMOUNT": 1
    },
    "load_ready": true
  },
  "records": [
    {
      "line_index": 1,
      "byte_row": "2026070001230012026032036-2026-0160-000   0160  VHA000014801002520D000000010000000         UDO - MEDICAL SUPPLIES                                                                                       ",
      "group": "JV-2026-000123",
      "outcome": "accepted",
      "reject_reason": null,
      "label": "JV 000123 / line 001 \u2014 UDO - MEDICAL SUPPLIES",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 1.",
          "detail": {
            "line_index": 1,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000123",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "480100",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000010000000",
            "vendor_id": "",
            "description": "UDO - MEDICAL SUPPLIES"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "ok",
          "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD\u2192ISO), money scaled to Decimal.",
          "detail": {
            "journal_id": "JV-2026-000123",
            "fiscal_year": 2026,
            "accounting_period": 7,
            "line_number": 1,
            "posting_date": "2026-02-01",
            "tafs": "036-2026-0160-000",
            "fund": "0160-OPS",
            "cost_center": "VHA00001",
            "ussgl_account": "480100",
            "budget_object_class": "2520",
            "debit_amount": "100000.00",
            "credit_amount": "0.00",
            "vendor_id": null,
            "description": "UDO - MEDICAL SUPPLIES",
            "source_system": "FMS"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "ok",
          "summary": "Conforms to the target contract; accepted.",
          "detail": {
            "accepted": true
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "ok",
          "summary": "Belongs to journal JV-2026-000123.",
          "detail": {
            "journal": "JV-2026-000123",
            "group_state": {
              "debits": "100000.00",
              "credits": "100000.00",
              "balanced": true,
              "variance": "0.00"
            }
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "ok",
          "summary": "Emitted to the pipe-delimited Momentum load file.",
          "detail": {
            "wire": "JV-2026-000123|2026|7|1|2026-02-01|036-2026-0160-000|0160-OPS|VHA00001|480100|2520|100000.00|0.00||UDO - MEDICAL SUPPLIES|FMS"
          }
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "ok",
          "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
          "detail": {
            "load_status": "loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 2,
      "byte_row": "2026070001230022026032036-2026-0160-000   0160  VHA000012110002520C000000010000000         ACCOUNTS PAYABLE - MED SUPPLIES                                                                              ",
      "group": "JV-2026-000123",
      "outcome": "accepted",
      "reject_reason": null,
      "label": "JV 000123 / line 002 \u2014 ACCOUNTS PAYABLE - MED SUPPLIES",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 2.",
          "detail": {
            "line_index": 2,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000123",
            "line_no": "002",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "211000",
            "budget_obj_class": "2520",
            "dr_cr_ind": "C",
            "amount": "000000010000000",
            "vendor_id": "",
            "description": "ACCOUNTS PAYABLE - MED SUPPLIES"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "ok",
          "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD\u2192ISO), money scaled to Decimal.",
          "detail": {
            "journal_id": "JV-2026-000123",
            "fiscal_year": 2026,
            "accounting_period": 7,
            "line_number": 2,
            "posting_date": "2026-02-01",
            "tafs": "036-2026-0160-000",
            "fund": "0160-OPS",
            "cost_center": "VHA00001",
            "ussgl_account": "211000",
            "budget_object_class": "2520",
            "debit_amount": "0.00",
            "credit_amount": "100000.00",
            "vendor_id": null,
            "description": "ACCOUNTS PAYABLE - MED SUPPLIES",
            "source_system": "FMS"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "ok",
          "summary": "Conforms to the target contract; accepted.",
          "detail": {
            "accepted": true
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "ok",
          "summary": "Belongs to journal JV-2026-000123.",
          "detail": {
            "journal": "JV-2026-000123",
            "group_state": {
              "debits": "100000.00",
              "credits": "100000.00",
              "balanced": true,
              "variance": "0.00"
            }
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "ok",
          "summary": "Emitted to the pipe-delimited Momentum load file.",
          "detail": {
            "wire": "JV-2026-000123|2026|7|2|2026-02-01|036-2026-0160-000|0160-OPS|VHA00001|211000|2520|0.00|100000.00||ACCOUNTS PAYABLE - MED SUPPLIES|FMS"
          }
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "ok",
          "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
          "detail": {
            "load_status": "loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 3,
      "byte_row": "2026070001240012026032036-2026-0162-000   0162  VHA000016100002520D000000006000000         PROGRAM COST - PROSTHETICS                                                                                   ",
      "group": "JV-2026-000124",
      "outcome": "accepted",
      "reject_reason": null,
      "label": "JV 000124 / line 001 \u2014 PROGRAM COST - PROSTHETICS",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 3.",
          "detail": {
            "line_index": 3,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000124",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0162-000",
            "fund": "0162",
            "cost_center": "VHA00001",
            "ussgl_acct": "610000",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000006000000",
            "vendor_id": "",
            "description": "PROGRAM COST - PROSTHETICS"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "ok",
          "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD\u2192ISO), money scaled to Decimal.",
          "detail": {
            "journal_id": "JV-2026-000124",
            "fiscal_year": 2026,
            "accounting_period": 7,
            "line_number": 1,
            "posting_date": "2026-02-01",
            "tafs": "036-2026-0162-000",
            "fund": "0162-MEDSVC",
            "cost_center": "VHA00001",
            "ussgl_account": "610000",
            "budget_object_class": "2520",
            "debit_amount": "60000.00",
            "credit_amount": "0.00",
            "vendor_id": null,
            "description": "PROGRAM COST - PROSTHETICS",
            "source_system": "FMS"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "ok",
          "summary": "Conforms to the target contract; accepted.",
          "detail": {
            "accepted": true
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "ok",
          "summary": "Belongs to journal JV-2026-000124.",
          "detail": {
            "journal": "JV-2026-000124",
            "group_state": {
              "debits": "100000.00",
              "credits": "100000.00",
              "balanced": true,
              "variance": "0.00"
            }
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "ok",
          "summary": "Emitted to the pipe-delimited Momentum load file.",
          "detail": {
            "wire": "JV-2026-000124|2026|7|1|2026-02-01|036-2026-0162-000|0162-MEDSVC|VHA00001|610000|2520|60000.00|0.00||PROGRAM COST - PROSTHETICS|FMS"
          }
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "ok",
          "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
          "detail": {
            "load_status": "loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 4,
      "byte_row": "2026070001240022026032036-2026-0162-000   0162  VHA000016100002520D000000004000000         PROGRAM COST - PHARMACY                                                                                      ",
      "group": "JV-2026-000124",
      "outcome": "accepted",
      "reject_reason": null,
      "label": "JV 000124 / line 002 \u2014 PROGRAM COST - PHARMACY",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 4.",
          "detail": {
            "line_index": 4,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000124",
            "line_no": "002",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0162-000",
            "fund": "0162",
            "cost_center": "VHA00001",
            "ussgl_acct": "610000",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000004000000",
            "vendor_id": "",
            "description": "PROGRAM COST - PHARMACY"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "ok",
          "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD\u2192ISO), money scaled to Decimal.",
          "detail": {
            "journal_id": "JV-2026-000124",
            "fiscal_year": 2026,
            "accounting_period": 7,
            "line_number": 2,
            "posting_date": "2026-02-01",
            "tafs": "036-2026-0162-000",
            "fund": "0162-MEDSVC",
            "cost_center": "VHA00001",
            "ussgl_account": "610000",
            "budget_object_class": "2520",
            "debit_amount": "40000.00",
            "credit_amount": "0.00",
            "vendor_id": null,
            "description": "PROGRAM COST - PHARMACY",
            "source_system": "FMS"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "ok",
          "summary": "Conforms to the target contract; accepted.",
          "detail": {
            "accepted": true
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "ok",
          "summary": "Belongs to journal JV-2026-000124.",
          "detail": {
            "journal": "JV-2026-000124",
            "group_state": {
              "debits": "100000.00",
              "credits": "100000.00",
              "balanced": true,
              "variance": "0.00"
            }
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "ok",
          "summary": "Emitted to the pipe-delimited Momentum load file.",
          "detail": {
            "wire": "JV-2026-000124|2026|7|2|2026-02-01|036-2026-0162-000|0162-MEDSVC|VHA00001|610000|2520|40000.00|0.00||PROGRAM COST - PHARMACY|FMS"
          }
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "ok",
          "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
          "detail": {
            "load_status": "loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 5,
      "byte_row": "2026070001240032026032036-2026-0162-000   0162  VHA000011010002520C000000007000000         FBWT DRAWDOWN A                                                                                              ",
      "group": "JV-2026-000124",
      "outcome": "accepted",
      "reject_reason": null,
      "label": "JV 000124 / line 003 \u2014 FBWT DRAWDOWN A",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 5.",
          "detail": {
            "line_index": 5,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000124",
            "line_no": "003",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0162-000",
            "fund": "0162",
            "cost_center": "VHA00001",
            "ussgl_acct": "101000",
            "budget_obj_class": "2520",
            "dr_cr_ind": "C",
            "amount": "000000007000000",
            "vendor_id": "",
            "description": "FBWT DRAWDOWN A"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "ok",
          "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD\u2192ISO), money scaled to Decimal.",
          "detail": {
            "journal_id": "JV-2026-000124",
            "fiscal_year": 2026,
            "accounting_period": 7,
            "line_number": 3,
            "posting_date": "2026-02-01",
            "tafs": "036-2026-0162-000",
            "fund": "0162-MEDSVC",
            "cost_center": "VHA00001",
            "ussgl_account": "101000",
            "budget_object_class": "2520",
            "debit_amount": "0.00",
            "credit_amount": "70000.00",
            "vendor_id": null,
            "description": "FBWT DRAWDOWN A",
            "source_system": "FMS"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "ok",
          "summary": "Conforms to the target contract; accepted.",
          "detail": {
            "accepted": true
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "ok",
          "summary": "Belongs to journal JV-2026-000124.",
          "detail": {
            "journal": "JV-2026-000124",
            "group_state": {
              "debits": "100000.00",
              "credits": "100000.00",
              "balanced": true,
              "variance": "0.00"
            }
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "ok",
          "summary": "Emitted to the pipe-delimited Momentum load file.",
          "detail": {
            "wire": "JV-2026-000124|2026|7|3|2026-02-01|036-2026-0162-000|0162-MEDSVC|VHA00001|101000|2520|0.00|70000.00||FBWT DRAWDOWN A|FMS"
          }
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "ok",
          "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
          "detail": {
            "load_status": "loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 6,
      "byte_row": "2026070001240042026032036-2026-0162-000   0162  VHA000011010002520C000000003000000         FBWT DRAWDOWN B                                                                                              ",
      "group": "JV-2026-000124",
      "outcome": "accepted",
      "reject_reason": null,
      "label": "JV 000124 / line 004 \u2014 FBWT DRAWDOWN B",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 6.",
          "detail": {
            "line_index": 6,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000124",
            "line_no": "004",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0162-000",
            "fund": "0162",
            "cost_center": "VHA00001",
            "ussgl_acct": "101000",
            "budget_obj_class": "2520",
            "dr_cr_ind": "C",
            "amount": "000000003000000",
            "vendor_id": "",
            "description": "FBWT DRAWDOWN B"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "ok",
          "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD\u2192ISO), money scaled to Decimal.",
          "detail": {
            "journal_id": "JV-2026-000124",
            "fiscal_year": 2026,
            "accounting_period": 7,
            "line_number": 4,
            "posting_date": "2026-02-01",
            "tafs": "036-2026-0162-000",
            "fund": "0162-MEDSVC",
            "cost_center": "VHA00001",
            "ussgl_account": "101000",
            "budget_object_class": "2520",
            "debit_amount": "0.00",
            "credit_amount": "30000.00",
            "vendor_id": null,
            "description": "FBWT DRAWDOWN B",
            "source_system": "FMS"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "ok",
          "summary": "Conforms to the target contract; accepted.",
          "detail": {
            "accepted": true
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "ok",
          "summary": "Belongs to journal JV-2026-000124.",
          "detail": {
            "journal": "JV-2026-000124",
            "group_state": {
              "debits": "100000.00",
              "credits": "100000.00",
              "balanced": true,
              "variance": "0.00"
            }
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "ok",
          "summary": "Emitted to the pipe-delimited Momentum load file.",
          "detail": {
            "wire": "JV-2026-000124|2026|7|4|2026-02-01|036-2026-0162-000|0162-MEDSVC|VHA00001|101000|2520|0.00|30000.00||FBWT DRAWDOWN B|FMS"
          }
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "ok",
          "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
          "detail": {
            "load_status": "loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 7,
      "byte_row": "2026070002000012026032036-2026-0160-000   0160  VHA000019999992520D000000000050000         BAD USSGL ACCOUNT                                                                                            ",
      "group": null,
      "outcome": "rejected",
      "reject_reason": "BAD_USSGL",
      "label": "JV 000200 / line 001 \u2014 BAD USSGL ACCOUNT",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 7.",
          "detail": {
            "line_index": 7,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000200",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "999999",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000000050000",
            "vendor_id": "",
            "description": "BAD USSGL ACCOUNT"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "halt",
          "summary": "Transform halted \u2014 a contract rule failed before a full target line could be built.",
          "detail": {
            "reason": "BAD_USSGL",
            "detail": "ussgl='999999'"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "reject",
          "summary": "REJECTED \u2014 BAD_USSGL",
          "detail": {
            "reason": "BAD_USSGL",
            "detail": "ussgl='999999'"
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "reject",
          "summary": "Excluded from the target batch (counted as rejected, never dropped).",
          "detail": {
            "counted_as": "rejected"
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "skip",
          "summary": "Not emitted (rejected at S3).",
          "detail": {}
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "skip",
          "summary": "Not presented to the load (rejected upstream).",
          "detail": {
            "load_status": "not_loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 8,
      "byte_row": "2026070002010012026032036-2026-0160-000   0160  VHA000014801002520D000000000000000         ZERO DOLLAR FILLER                                                                                           ",
      "group": null,
      "outcome": "rejected",
      "reject_reason": "ZERO_AMOUNT",
      "label": "JV 000201 / line 001 \u2014 ZERO DOLLAR FILLER",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 8.",
          "detail": {
            "line_index": 8,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000201",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "480100",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000000000000",
            "vendor_id": "",
            "description": "ZERO DOLLAR FILLER"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "halt",
          "summary": "Transform halted \u2014 a contract rule failed before a full target line could be built.",
          "detail": {
            "reason": "ZERO_AMOUNT",
            "detail": "amount=0.00"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "reject",
          "summary": "REJECTED \u2014 ZERO_AMOUNT",
          "detail": {
            "reason": "ZERO_AMOUNT",
            "detail": "amount=0.00"
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "reject",
          "summary": "Excluded from the target batch (counted as rejected, never dropped).",
          "detail": {
            "counted_as": "rejected"
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "skip",
          "summary": "Not emitted (rejected at S3).",
          "detail": {}
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "skip",
          "summary": "Not presented to the load (rejected upstream).",
          "detail": {
            "load_status": "not_loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 9,
      "byte_row": "2026070002020012026032036-2026-0160-000   0160  VHA000014801002520X000000000001000         BAD DR CR INDICATOR                                                                                          ",
      "group": null,
      "outcome": "rejected",
      "reject_reason": "BAD_DR_CR",
      "label": "JV 000202 / line 001 \u2014 BAD DR CR INDICATOR",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 9.",
          "detail": {
            "line_index": 9,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000202",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "480100",
            "budget_obj_class": "2520",
            "dr_cr_ind": "X",
            "amount": "000000000001000",
            "vendor_id": "",
            "description": "BAD DR CR INDICATOR"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "halt",
          "summary": "Transform halted \u2014 a contract rule failed before a full target line could be built.",
          "detail": {
            "reason": "BAD_DR_CR",
            "detail": "ind='X'"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "reject",
          "summary": "REJECTED \u2014 BAD_DR_CR",
          "detail": {
            "reason": "BAD_DR_CR",
            "detail": "ind='X'"
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "reject",
          "summary": "Excluded from the target batch (counted as rejected, never dropped).",
          "detail": {
            "counted_as": "rejected"
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "skip",
          "summary": "Not emitted (rejected at S3).",
          "detail": {}
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "skip",
          "summary": "Not presented to the load (rejected upstream).",
          "detail": {
            "load_status": "not_loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 10,
      "byte_row": "2026070002030012026400036-2026-0160-000   0160  VHA000014801002520D000000000001000         BAD JULIAN DATE                                                                                              ",
      "group": null,
      "outcome": "rejected",
      "reject_reason": "BAD_DATE",
      "label": "JV 000203 / line 001 \u2014 BAD JULIAN DATE",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 10.",
          "detail": {
            "line_index": 10,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000203",
            "line_no": "001",
            "post_date_jul": "2026400",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "480100",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000000001000",
            "vendor_id": "",
            "description": "BAD JULIAN DATE"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "halt",
          "summary": "Transform halted \u2014 a contract rule failed before a full target line could be built.",
          "detail": {
            "reason": "BAD_DATE",
            "detail": "jul='2026400'"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "reject",
          "summary": "REJECTED \u2014 BAD_DATE",
          "detail": {
            "reason": "BAD_DATE",
            "detail": "jul='2026400'"
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "reject",
          "summary": "Excluded from the target batch (counted as rejected, never dropped).",
          "detail": {
            "counted_as": "rejected"
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "skip",
          "summary": "Not emitted (rejected at S3).",
          "detail": {}
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "skip",
          "summary": "Not presented to the load (rejected upstream).",
          "detail": {
            "load_status": "not_loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 11,
      "byte_row": "2026070002040012026032036-2026-0160-000   9999  VHA000014801002520D000000000001000         UNMAPPED FUND                                                                                                ",
      "group": null,
      "outcome": "rejected",
      "reject_reason": "BAD_FUND",
      "label": "JV 000204 / line 001 \u2014 UNMAPPED FUND",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 11.",
          "detail": {
            "line_index": 11,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000204",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "9999",
            "cost_center": "VHA00001",
            "ussgl_acct": "480100",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "000000000001000",
            "vendor_id": "",
            "description": "UNMAPPED FUND"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "halt",
          "summary": "Transform halted \u2014 a contract rule failed before a full target line could be built.",
          "detail": {
            "reason": "BAD_FUND",
            "detail": "unmapped fund='9999'"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "reject",
          "summary": "REJECTED \u2014 BAD_FUND",
          "detail": {
            "reason": "BAD_FUND",
            "detail": "unmapped fund='9999'"
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "reject",
          "summary": "Excluded from the target batch (counted as rejected, never dropped).",
          "detail": {
            "counted_as": "rejected"
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "skip",
          "summary": "Not emitted (rejected at S3).",
          "detail": {}
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "skip",
          "summary": "Not presented to the load (rejected upstream).",
          "detail": {
            "load_status": "not_loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    },
    {
      "line_index": 12,
      "byte_row": "2026070002050012026032036-2026-0160-000   0160  VHA000014801002520DABC000000000000         NON NUMERIC AMOUNT                                                                                           ",
      "group": null,
      "outcome": "rejected",
      "reject_reason": "NON_NUMERIC",
      "label": "JV 000205 / line 001 \u2014 NON NUMERIC AMOUNT",
      "stages": [
        {
          "id": "S0",
          "name": "Profile / parse",
          "status": "ok",
          "summary": "Parsed 12-record extract; this is byte-row 12.",
          "detail": {
            "line_index": 12,
            "fiscal_year": "2026",
            "acct_period": "07",
            "jv_number": "000205",
            "line_no": "001",
            "post_date_jul": "2026032",
            "treasury_symbol": "036-2026-0160-000",
            "fund": "0160",
            "cost_center": "VHA00001",
            "ussgl_acct": "480100",
            "budget_obj_class": "2520",
            "dr_cr_ind": "D",
            "amount": "ABC000000000000",
            "vendor_id": "",
            "description": "NON NUMERIC AMOUNT"
          }
        },
        {
          "id": "S1",
          "name": "Bind contract",
          "status": "ok",
          "summary": "Target contract: MOMENTUM-JOURNAL-IMPORT (source_system=FMS).",
          "detail": {
            "target_contract": "MOMENTUM-JOURNAL-IMPORT"
          }
        },
        {
          "id": "S2",
          "name": "Map / transform",
          "status": "halt",
          "summary": "Transform halted \u2014 a contract rule failed before a full target line could be built.",
          "detail": {
            "reason": "NON_NUMERIC",
            "detail": "amount='ABC000000000000'"
          }
        },
        {
          "id": "S3",
          "name": "Validate",
          "status": "reject",
          "summary": "REJECTED \u2014 NON_NUMERIC",
          "detail": {
            "reason": "NON_NUMERIC",
            "detail": "amount='ABC000000000000'"
          }
        },
        {
          "id": "S4",
          "name": "Reconcile",
          "status": "reject",
          "summary": "Excluded from the target batch (counted as rejected, never dropped).",
          "detail": {
            "counted_as": "rejected"
          }
        },
        {
          "id": "S5",
          "name": "Emit",
          "status": "skip",
          "summary": "Not emitted (rejected at S3).",
          "detail": {}
        },
        {
          "id": "S6",
          "name": "Load-simulate",
          "status": "skip",
          "summary": "Not presented to the load (rejected upstream).",
          "detail": {
            "load_status": "not_loaded"
          }
        },
        {
          "id": "S7",
          "name": "Test / gate",
          "status": "ok",
          "summary": "Batch passed all control gates (row accounting, $ control total, journal balance).",
          "detail": {
            "batch_load_ready": true
          }
        }
      ]
    }
  ]
};
