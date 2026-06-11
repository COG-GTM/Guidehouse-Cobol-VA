window.ICD_DATA = {
  "title_page": {
    "interface_name": "FMS Obligation/Disbursement Extract -> iFAMS (Momentum) Obligation Import",
    "document_date": "2026-06-11",
    "classification_banner": "Controlled Unclassified Information, Pre-Decisional, Internal VA Use Only - Working DRAFT"
  },
  "versions": [
    {
      "sequence_number": "1.0",
      "status": "Draft",
      "author": "Integration & Conversion Factory (generated)",
      "date": "2026-06-11",
      "change_summary": "Initial generated draft from the obligation/disbursement conversion slice."
    }
  ],
  "executive_summary": {
    "business_context": "VA FMBT is migrating core financial management from the legacy FMS to iFAMS (CGI Momentum). The obligation/disbursement spending chain is the highest-stakes data family in that migration: disbursing beyond obligated authority is an Antideficiency-Act-class finding.",
    "integration_objective": "Convert the daily FMS obligation/disbursement extract into the Momentum obligation-import contract with provable correctness: row accounting, dollar control totals to the cent, per-obligation funding gates, and a typed reject ledger with no silent drops.",
    "stakeholder_summary": "VA OFM/Finance (business owner), FMBT ID&C team (interface delivery), CGI SI team (Momentum target), Guidehouse + Cognition (integration & conversion factory), interface partner system owners."
  },
  "purpose_statement": "This ICD defines the data exchange between the legacy FMS obligation/disbursement extract and the iFAMS (Momentum) obligation import, including mapping, controls, reconciliation, and error handling.",
  "in_scope_items": [
    "Daily FMS obligation and disbursement extract file (fixed-width, OBL-DISBURSEMENT-REC layout)",
    "Transformation to the Momentum obligation-import pipe-delimited contract",
    "Reconciliation evidence: row accounting, $ control totals, per-obligation funding gate",
    "Typed reject ledger and resubmission flow"
  ],
  "out_of_scope_items": [
    "Application logic modernization (CACI lane)",
    "Momentum platform configuration (CGI lane)",
    "Non-financial interfaces of the partner system"
  ],
  "assumptions": [
    "Interface is outbound-only from FMS to iFAMS (one direction, file-based).",
    "SFTP transport via the VA ESB is available in all environments.",
    "The Momentum obligation-import contract version is stable within a wave.",
    "Synthetic reference data (USSGL whitelist, fund crosswalk) will be replaced by authoritative fiscal-year charts before production cutover (open questions Q-REF-1, Q-REF-2)."
  ],
  "constraints": [
    "Batch window: extract must complete load simulation before the Momentum nightly import cutoff.",
    "All money handled as Decimal; control totals compared to the cent.",
    "No production data in this repository; all fixtures are synthetic."
  ],
  "acknowledgements": [
    {
      "item": "Authoritative Momentum import contract (ICD) not yet supplied by CGI.",
      "proposed_resolution": "Tracked as open questions Q-MOM-1/Q-MOM-2; generated contract used as stand-in."
    }
  ],
  "pocs": [
    {
      "name": "TBD-SME",
      "email": "tbd-sme@va.gov",
      "position": "Interface Partner functional POC",
      "organization": "VA"
    },
    {
      "name": "TBD-SME",
      "email": "tbd-sme@va.gov",
      "position": "ID&C technical POC",
      "organization": "FMBT ID&C"
    }
  ],
  "wave_label": "Wave TBD-CUSTOMER (assignment pending volume data)",
  "wave_specific_additions": [],
  "terms": [
    {
      "term": "CSV",
      "definition": "Comma-separated values file format."
    },
    {
      "term": "Data Element",
      "definition": "A discrete unit of data with a defined format and meaning."
    },
    {
      "term": "ESB",
      "definition": "Enterprise Service Bus \u2014 VA's integration middleware."
    },
    {
      "term": "iFAMS",
      "definition": "Integrated Financial and Acquisition Management System (CGI Momentum)."
    },
    {
      "term": "SFTP",
      "definition": "Secure File Transfer Protocol."
    },
    {
      "term": "USSGL",
      "definition": "United States Standard General Ledger."
    },
    {
      "term": "TAFS",
      "definition": "Treasury Appropriation Fund Symbol."
    }
  ],
  "operational_agreement_text": "This interface is required because FMS is being decommissioned under FMBT and its obligation/disbursement data must continue to post to the VA's system of record (iFAMS) without interruption to spending-chain integrity or audit compliance.",
  "references": [
    {
      "title": "FMBT_ICD-AEI-Sample.docx (customer ICD automation spec)",
      "relevance": "Defines the required structure and validation rules of this document."
    },
    {
      "title": "VA FMBT - FMS and iFAMS Interface Systems.xlsx (customer inventory)",
      "relevance": "Portfolio context: places this interface within the 62-system factory scope."
    },
    {
      "title": "factory/conversion-datasets/obligation-disbursement/",
      "relevance": "Runnable conversion slice this ICD is generated from."
    }
  ],
  "va_system": {
    "system_name": "FMS (Financial Management System) \u2014 obligation/disbursement subsystem",
    "system_function_summary": "Legacy VA core financial system recording obligations and disbursements against appropriated funds; produces a daily fixed-width extract of spending-chain activity.",
    "technical_platform_summary": "Mainframe COBOL/Pro*COBOL batch processing with fixed-width record layouts (OBL-DISBURSEMENT-REC copybook) and Oracle persistence."
  },
  "ifams_systems": {
    "ifams_functions_summary": "iFAMS (CGI Momentum SaaS on Azure) is the FM QSMO-approved target platform; it ingests obligation documents via its batch import contracts and enforces funds control.",
    "esb_functions": [
      "Proxy submission of extract files from the partner boundary",
      "Transport logging and delivery acknowledgement",
      "SFTP endpoint hosting and routing to the Momentum import landing zone"
    ]
  },
  "legacy_process_description": "FMS nightly batch produces the obligation/disbursement extract; legacy jobs validate and post to FMS ledgers. Downstream consumers receive flat-file copies.",
  "future_process_description": "The factory converts the same extract through parse -> map/validate -> reconcile -> emit -> simulated load. Accepted lines are emitted in the Momentum obligation-import wire format; rejects land in a typed ledger for source-system correction and resubmission.",
  "operations": [
    {
      "id": "OP-1",
      "name": "Daily obligation/disbursement load",
      "purpose": "Convert and load the daily FMS extract into Momentum.",
      "trigger": "time",
      "direction": "outbound",
      "interfaces_impacted": [
        "Momentum obligation import"
      ]
    },
    {
      "id": "OP-2",
      "name": "Reject resubmission",
      "purpose": "Reprocess corrected records after source-system fix.",
      "trigger": "event",
      "direction": "outbound",
      "interfaces_impacted": [
        "Momentum obligation import"
      ]
    }
  ],
  "transfer_mechanisms": [
    {
      "protocol": "SFTP",
      "routing": "FMS batch -> VA ESB -> Momentum import landing zone",
      "packaging": "pipe-delimited",
      "connectivity_diagram_ref": ""
    }
  ],
  "transaction_types": [
    {
      "name": "OBLIGATION",
      "usage": "Establishes/increases obligated authority for a document line.",
      "frequency": "Daily batch",
      "volume_estimate": "TBD-CUSTOMER (no volume data in customer inventory)"
    },
    {
      "name": "DISBURSEMENT",
      "usage": "Records outlays against an existing obligation.",
      "frequency": "Daily batch",
      "volume_estimate": "TBD-CUSTOMER (no volume data in customer inventory)"
    }
  ],
  "data_exchanges": [
    {
      "producer": "FMS",
      "consumer": "iFAMS (Momentum obligation import)",
      "format": "pipe-delimited per MOMENTUM-OBLIGATION-IMPORT contract",
      "schedule": "Daily, post-FMS-nightly-batch",
      "acknowledgement": "yes"
    }
  ],
  "data_compliance": {
    "compliance_strategy": "All emitted values conform to iFAMS reference data: USSGL accounts validated against the fiscal-year chart, legacy funds mapped through the authoritative crosswalk, dates normalized to ISO-8601. Non-conforming records are rejected with typed reasons, never transformed by guess.",
    "uses_ifams_codes": true,
    "noncompliance_justification": "",
    "compliance_timeline": "Per-wave cutover"
  },
  "precedence_rules": [
    "Obligation lines for a document load before disbursement lines (funding gate dependency).",
    "Rejected lines never block accepted lines in the same batch."
  ],
  "criticality_levels": [
    "High \u2014 spending-chain integrity; failed loads can stop disbursement processing and create ADA exposure."
  ],
  "comm_methods": [
    "SFTP (batch file)",
    "Email notification of batch disposition (ESB)"
  ],
  "security_requirements": [
    {
      "id": "SEC-1",
      "requirement": "Encrypt all interface traffic in transit.",
      "implementation_detail": "SFTP (SSH2) between partner boundary, ESB, and Momentum landing zone.",
      "transmission_medium": "VA network / ESB SFTP",
      "data_protection": "TLS/SSH encryption in transit; CUI handling at rest",
      "auditability": "ESB transfer logs retained per VA records schedule"
    },
    {
      "id": "SEC-2",
      "requirement": "No credentials in code or files.",
      "implementation_detail": "Managed secrets for SFTP/service accounts; parameterized DB access.",
      "transmission_medium": "n/a",
      "data_protection": "Secrets manager, least privilege",
      "auditability": "Access logging on secret retrieval"
    }
  ],
  "logging_by_platform": [
    {
      "platform": "SYSTEM",
      "logging_detail": "FMS batch job logs: extract row counts and $ totals.",
      "audit_detail": "Batch control report retained with the extract.",
      "poc": "TBD-SME",
      "monitoring_instructions": "Compare extract control totals to factory recon report."
    },
    {
      "platform": "ESB",
      "logging_detail": "Transfer logs: file name, size, checksum, timestamps.",
      "audit_detail": "Delivery acknowledgement records.",
      "poc": "TBD-SME",
      "monitoring_instructions": "Alert on missing daily file by cutoff time."
    },
    {
      "platform": "iFAMS",
      "logging_detail": "Momentum import job log: accepted/rejected counts.",
      "audit_detail": "Import batch audit trail keyed by batch id.",
      "poc": "TBD-SME",
      "monitoring_instructions": "Reconcile Momentum-loaded totals to factory emit totals."
    }
  ],
  "volume_matrix": [
    {
      "service_name": "Daily obligation/disbursement load",
      "transaction_volume": "TBD-CUSTOMER (gap: customer inventory has no volumes)",
      "line_counts": "TBD-CUSTOMER",
      "hours_of_operation": "Nightly batch window (ET)",
      "frequency": "Daily"
    }
  ],
  "peak_periods": [
    "Fiscal year-end (September): expect multiples of typical daily volume (quantification pending customer data).",
    "Month-end close: elevated correction/resubmission traffic."
  ],
  "contention_analysis": "Same-document collisions are possible when an obligation modification and a disbursement for one document arrive in the same batch.",
  "mitigations": [
    "Deterministic intra-batch ordering: obligations before disbursements per document.",
    "Idempotent restart: re-running a batch cannot double-post (natural-key de-duplication)."
  ],
  "performance_requirements": [
    {
      "id": "PERF-1",
      "requirement_text": "Daily extract converted, reconciled, and load-simulated within the batch window.",
      "metric": "End-to-end conversion wall-clock time",
      "threshold": "Within nightly window ahead of Momentum import cutoff",
      "measurement_method": "Factory run telemetry per batch"
    }
  ],
  "priorities": [
    "Spending-chain integrity over throughput",
    "Reject visibility over auto-correction"
  ],
  "dependencies": [
    "FMS nightly batch completion",
    "ESB SFTP availability",
    "Momentum import window"
  ],
  "availability_matrix": [
    {
      "system": "iFAMS",
      "availability": "Per CGI Momentum SaaS SLA",
      "maintenance_window": "TBD-CUSTOMER",
      "scheduled_outage_process": "Hold-and-queue at ESB"
    },
    {
      "system": "ESB",
      "availability": "24x7 with maintenance windows",
      "maintenance_window": "TBD-CUSTOMER",
      "scheduled_outage_process": "Retransmit after window"
    },
    {
      "system": "FMS",
      "availability": "Nightly batch",
      "maintenance_window": "TBD-CUSTOMER",
      "scheduled_outage_process": "Next-day catch-up batch"
    }
  ],
  "runbook_entries": [
    {
      "job_name": "FCT-OBL-DAILY",
      "schedule": "TBD-SME (align to FMS nightly batch completion)",
      "preconditions": "FMS extract present and checksum-verified",
      "file_locations": "ESB landing zone (path per environment connect procedure)",
      "expected_counts": "Must equal FMS batch control report counts",
      "escalation_steps": "TBD-SME on-call rotation",
      "holiday_exceptions": "TBD-SME"
    }
  ],
  "upgrade_topics": [
    {
      "area": "Momentum import contract version",
      "impact": "Field additions/renames change the emit contract.",
      "action_required": "Regenerate mapping + this ICD from the updated contract; rerun golden-file regression."
    }
  ],
  "error_handling_matrix": [
    {
      "service_name": "Daily obligation/disbursement load",
      "platform": "SYSTEM",
      "detection_method": "Factory mapper validation (typed reject reasons)",
      "common_error_codes": [
        "BAD_DATE",
        "BAD_FUND",
        "BAD_PERIOD",
        "BAD_POP",
        "BAD_TXN_TYPE",
        "BAD_USSGL",
        "MISSING_OBLIGATION_NO",
        "MISSING_VENDOR",
        "NON_NUMERIC",
        "ZERO_AMOUNT"
      ],
      "correction_process": "Correct in FMS source data; never hand-edit the extract.",
      "resubmission_method": "Corrected records included in next daily extract or ad-hoc resubmission batch",
      "responsible_team": "Interface Partner + Finance"
    },
    {
      "service_name": "Daily obligation/disbursement load",
      "platform": "ESB",
      "detection_method": "Missing-file and checksum alerts",
      "common_error_codes": [
        "TRANSFER_TIMEOUT",
        "CHECKSUM_MISMATCH"
      ],
      "correction_process": "Retransmit from source",
      "resubmission_method": "ESB-managed retry",
      "responsible_team": "ESB operations"
    },
    {
      "service_name": "Daily obligation/disbursement load",
      "platform": "iFAMS",
      "detection_method": "Momentum import job status + post-load reconciliation",
      "common_error_codes": [
        "IMPORT_REJECT",
        "FUNDS_CONTROL_FAIL"
      ],
      "correction_process": "Triage against factory recon report; correct at source",
      "resubmission_method": "Resubmit corrected batch",
      "responsible_team": "ID&C + CGI SI"
    }
  ],
  "recon_strategies": [
    {
      "scope": "file-level",
      "control_totals_used": "lines_in == loaded + rejected; obligation $ and disbursement $ totals to the cent (legacy vs emitted)",
      "reports": "Factory reconciliation report (JSON) per batch",
      "frequency": "Every batch (daily)",
      "owner": "Integration & Conversion Factory"
    },
    {
      "scope": "transaction-level",
      "control_totals_used": "Per-obligation funding gate: sum(disbursements) <= sum(obligations) per document",
      "reports": "Funding-gate section of the reconciliation report; reject ledger",
      "frequency": "Every batch (daily)",
      "owner": "Finance (review) + Factory (produce)"
    }
  ],
  "troubleshooting_entries": [
    {
      "symptom": "Batch exits non-zero / not load-ready",
      "probable_cause": "Control-total mismatch or funding-gate trip",
      "steps_to_resolve": "Read reconciliation report; triage rejects by typed reason; correct at source.",
      "references": [
        "factory/playbooks/02-reconciliation-test-harness.md"
      ],
      "escalation_contact": "TBD-SME"
    }
  ],
  "message_exchanges": [
    {
      "id": "MX-1",
      "name": "Obligation/disbursement daily file",
      "direction": "outbound",
      "format": "pipe-delimited (MOMENTUM-OBLIGATION-IMPORT)",
      "trigger": "FMS nightly batch completion",
      "acknowledgement": "ESB delivery ack + Momentum import disposition",
      "success_criteria": "Batch load-ready: rows reconcile, $ totals match, every journal/funding gate passes"
    }
  ],
  "file_mapping": [
    {
      "system_field_name": "FMS.OBLIGATION_ID",
      "ifams_field_name": "obligation_id",
      "description": "Legacy FMS obligation document number (natural key)",
      "ifams_table_field": "OBL_IMPORT.OBLIGATION_ID",
      "position": 1,
      "max_length": 14,
      "format": "CHAR",
      "notes": ""
    },
    {
      "system_field_name": "FMS.FISCAL_YEAR",
      "ifams_field_name": "fiscal_year",
      "description": "Posting fiscal year",
      "ifams_table_field": "OBL_IMPORT.FISCAL_YEAR",
      "position": 2,
      "max_length": 4,
      "format": "NUM CCYY",
      "notes": ""
    },
    {
      "system_field_name": "FMS.ACCOUNTING_PERIOD",
      "ifams_field_name": "accounting_period",
      "description": "Accounting period within fiscal year",
      "ifams_table_field": "OBL_IMPORT.ACCOUNTING_PERIOD",
      "position": 3,
      "max_length": 2,
      "format": "NUM 1-12",
      "notes": ""
    },
    {
      "system_field_name": "FMS.LINE_NUMBER",
      "ifams_field_name": "line_number",
      "description": "Line number within the obligation document",
      "ifams_table_field": "OBL_IMPORT.LINE_NUMBER",
      "position": 4,
      "max_length": 5,
      "format": "NUM",
      "notes": ""
    },
    {
      "system_field_name": "FMS.TXN_TYPE",
      "ifams_field_name": "txn_type",
      "description": "Canonical transaction type (OBLIGATION | DISBURSEMENT)",
      "ifams_table_field": "OBL_IMPORT.TXN_TYPE",
      "position": 5,
      "max_length": 12,
      "format": "ENUM",
      "notes": ""
    },
    {
      "system_field_name": "FMS.VENDOR_ID",
      "ifams_field_name": "vendor_id",
      "description": "Vendor identifier (synthetic; production = SAM UEI)",
      "ifams_table_field": "OBL_IMPORT.VENDOR_ID",
      "position": 6,
      "max_length": 12,
      "format": "CHAR",
      "notes": ""
    },
    {
      "system_field_name": "FMS.TAFS",
      "ifams_field_name": "tafs",
      "description": "Treasury Appropriation Fund Symbol",
      "ifams_table_field": "OBL_IMPORT.TAFS",
      "position": 7,
      "max_length": 21,
      "format": "CHAR",
      "notes": ""
    },
    {
      "system_field_name": "FMS.APPROPRIATION",
      "ifams_field_name": "appropriation",
      "description": "Momentum fund from the legacy fund crosswalk",
      "ifams_table_field": "OBL_IMPORT.APPROPRIATION",
      "position": 8,
      "max_length": 12,
      "format": "CHAR",
      "notes": ""
    },
    {
      "system_field_name": "FMS.OBJECT_CLASS",
      "ifams_field_name": "object_class",
      "description": "OMB object class of the spending",
      "ifams_table_field": "OBL_IMPORT.OBJECT_CLASS",
      "position": 9,
      "max_length": 3,
      "format": "NUM",
      "notes": ""
    },
    {
      "system_field_name": "FMS.USSGL_ACCOUNT",
      "ifams_field_name": "ussgl_account",
      "description": "USSGL account (validated against fiscal-year chart)",
      "ifams_table_field": "OBL_IMPORT.USSGL_ACCOUNT",
      "position": 10,
      "max_length": 6,
      "format": "NUM",
      "notes": ""
    },
    {
      "system_field_name": "FMS.OBLIGATION_AMOUNT",
      "ifams_field_name": "obligation_amount",
      "description": "Obligation amount (Decimal, 2dp)",
      "ifams_table_field": "OBL_IMPORT.OBLIGATION_AMOUNT",
      "position": 11,
      "max_length": 18,
      "format": "DEC 2dp",
      "notes": ""
    },
    {
      "system_field_name": "FMS.DISBURSEMENT_AMOUNT",
      "ifams_field_name": "disbursement_amount",
      "description": "Disbursement amount (Decimal, 2dp)",
      "ifams_table_field": "OBL_IMPORT.DISBURSEMENT_AMOUNT",
      "position": 12,
      "max_length": 18,
      "format": "DEC 2dp",
      "notes": ""
    },
    {
      "system_field_name": "FMS.POP_START_DATE",
      "ifams_field_name": "pop_start_date",
      "description": "Period-of-performance start",
      "ifams_table_field": "OBL_IMPORT.POP_START_DATE",
      "position": 13,
      "max_length": 10,
      "format": "ISO YYYY-MM-DD",
      "notes": ""
    },
    {
      "system_field_name": "FMS.POP_END_DATE",
      "ifams_field_name": "pop_end_date",
      "description": "Period-of-performance end",
      "ifams_table_field": "OBL_IMPORT.POP_END_DATE",
      "position": 14,
      "max_length": 10,
      "format": "ISO YYYY-MM-DD",
      "notes": ""
    },
    {
      "system_field_name": "FMS.TXN_DATE",
      "ifams_field_name": "txn_date",
      "description": "Transaction date (converted from legacy CCYYDDD)",
      "ifams_table_field": "OBL_IMPORT.TXN_DATE",
      "position": 15,
      "max_length": 10,
      "format": "ISO YYYY-MM-DD",
      "notes": ""
    },
    {
      "system_field_name": "FMS.DESCRIPTION",
      "ifams_field_name": "description",
      "description": "Free-text line description (pipe-stripped on emit)",
      "ifams_table_field": "OBL_IMPORT.DESCRIPTION",
      "position": 16,
      "max_length": 60,
      "format": "CHAR",
      "notes": ""
    },
    {
      "system_field_name": "FMS.SOURCE_SYSTEM",
      "ifams_field_name": "source_system",
      "description": "Originating legacy system tag",
      "ifams_table_field": "OBL_IMPORT.SOURCE_SYSTEM",
      "position": 17,
      "max_length": 8,
      "format": "CHAR",
      "notes": ""
    }
  ],
  "ws_mapping_note": "Not applicable \u2014 this interface is file-based. \u00a76.3 (web-service mapping) is retained in the template for SOAP/REST interfaces in the portfolio; no WSDL artifacts have been provided by the customer yet.",
  "service_requests": [],
  "service_responses": [],
  "verification_methods": [
    {
      "method": "Unit",
      "success_criteria": "Slice test suite green (parser, every reject reason, funding gate, round-trip)."
    },
    {
      "method": "Functional",
      "success_criteria": "Clean fixture converts load-ready (exit 0); seeded-defect fixture trips the gate (exit 1)."
    },
    {
      "method": "Load",
      "success_criteria": "Cutover-volume batch within window (TBD-CUSTOMER volumes)."
    },
    {
      "method": "SIT",
      "success_criteria": "End-to-end through ESB to Momentum test environment with acks."
    },
    {
      "method": "IST",
      "success_criteria": "Joint execution with CGI SI against Momentum import."
    },
    {
      "method": "End User Validation",
      "success_criteria": "Finance SME sign-off on reconciliation evidence."
    }
  ],
  "controls": [
    {
      "control_id": "IN-1.1",
      "control_activity": "Completeness of records transferred",
      "control_technique": "Row accounting invariant",
      "implementation_detail": "reconciliation.py asserts lines_in == accepted + rejected on every batch; CI gate fails otherwise."
    },
    {
      "control_id": "IN-1.2",
      "control_activity": "Accuracy of financial amounts",
      "control_technique": "Dollar control totals",
      "implementation_detail": "Legacy-side and emitted-side obligation/disbursement totals compared to the cent (Decimal, never float)."
    },
    {
      "control_id": "IN-2.1",
      "control_activity": "Funds control integrity",
      "control_technique": "Per-obligation funding gate",
      "implementation_detail": "sum(disbursements) <= sum(obligations) enforced per document pre-emit and re-asserted by the import simulator post-emit."
    },
    {
      "control_id": "IN-2.2",
      "control_activity": "Error visibility and resubmission",
      "control_technique": "Typed reject ledger",
      "implementation_detail": "Every rejected line carries a machine-readable reason code from the shared taxonomy; no silent drops."
    }
  ],
  "conversion_considerations": {
    "acs_link": "",
    "conversion_notes": "Legacy fund codes adopt the ACS crosswalk (stand-in FUND_CROSSWALK with 4 entries pending the authoritative crosswalk, Q-REF-2); USSGL validated against a 8-account stand-in chart (Q-REF-1); legacy CCYYDDD dates normalized to ISO.",
    "converted_data_interactions": "Yes \u2014 converted historical obligations must reconcile with daily interface postings so open-document balances remain correct across cutover."
  },
  "transition_steps": [
    "Run factory conversion in shadow mode against daily extracts; compare recon evidence to FMS control reports.",
    "Wave cutover: switch Momentum import to factory-emitted files; FMS posting disabled for the document family.",
    "Hypercare: daily reconciliation review with Finance for the first close cycle."
  ],
  "temporary_procedures": [
    "Manual journal entries for in-flight documents during the cutover weekend (Finance-approved)."
  ],
  "rollback_plan": "Factory emit is non-destructive: rollback = revert Momentum import to prior source and replay FMS posting; emitted batches are versioned and idempotent so no partial state persists.",
  "agility_link": "",
  "test_scripts": [
    {
      "id": "TS-1",
      "name": "Clean batch load rehearsal",
      "description": "convert.py on the clean synthetic fixture; expect exit 0, load_ready true."
    },
    {
      "id": "TS-2",
      "name": "Funding-gate trip",
      "description": "Fixture with disbursement > obligation; expect exit 1 and FUNDS_GATE finding."
    },
    {
      "id": "TS-3",
      "name": "Reject taxonomy coverage",
      "description": "Each typed reject reason exercised by at least one test record."
    }
  ],
  "open_items": [
    {
      "number": "OI-1",
      "status": "Open",
      "description": "Transaction volumes/frequency per interface not in customer inventory (needed for \u00a74.1 and wave sequencing).",
      "resolution": "",
      "impact": "Wave plan uses disposition heuristic; load testing thresholds unset."
    },
    {
      "number": "OI-2",
      "status": "Open",
      "description": "Authoritative Momentum import contract and reference data (Q-MOM-1/2, Q-REF-1/2) pending from CGI/VA.",
      "resolution": "",
      "impact": "Generated contract and stand-in crosswalks in use; swap is mechanical."
    },
    {
      "number": "OI-3",
      "status": "Open",
      "description": "Named POCs, runbook schedules, maintenance windows, and Agility links require SME input (TBD-SME/TBD-CUSTOMER markers).",
      "resolution": "",
      "impact": "Operational sections incomplete for production use; structure and controls complete."
    }
  ],
  "features": [
    {
      "feature_id": "F-1",
      "description": "Convert daily FMS obligation/disbursement extract to Momentum import with reconciliation evidence",
      "acceptance_criteria": [
        "Row accounting holds",
        "$ totals match to the cent",
        "Funding gate enforced",
        "Typed rejects only"
      ],
      "requirement_locations": [
        "\u00a75.2",
        "\u00a76.2",
        "\u00a78"
      ],
      "team_impact": "Both",
      "implemented_by": "Integration & Conversion Factory"
    }
  ],
  "metrics": {
    "fmbt_system_acronym": "FMS",
    "wave_interim_disposition": "MIGRATE_TO_IFAMS",
    "ifams_integration_recommendation": "Batch file import via ESB SFTP",
    "proposed_solution": "Factory-converted daily extract to Momentum obligation import",
    "owners": "Guidehouse + Cognition (factory); VA OFM (business)",
    "legacy_dev_required": false,
    "legacy_config_required": false
  },
  "custom_procedures": [],
  "environment_connect_steps": [
    "Exchange SFTP host keys / certificates between ESB and Momentum landing zone",
    "Open firewall rules for the environment's SFTP endpoint",
    "Enable the environment's import directory and verify with a zero-dollar test file"
  ]
};
