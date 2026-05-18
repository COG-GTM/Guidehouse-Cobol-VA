-- =====================================================================
-- LABD20 Extracted SQL Operations (Demo / Prep Output)
-- =====================================================================
-- Source:  source/procobol/LABD20.pco
-- Tables:  JC_SUBMITTED_COMMENT_TBL, JC_COUNT_TBL,
--          JC_REJECTED_COMMENT_TBL, JC_APPLIED_COMMENT_TBL
-- Purpose: Faithful, parameterized, Oracle-compatible SQL extracted from
--          LABD20's embedded EXEC SQL blocks, with citations back to the
--          original Pro*COBOL source lines and explanatory comments.
-- Style:   Bind variables use :upper_snake_case names instead of the
--          legacy :WS-...-... host variable names. The legacy names are
--          listed in the section comment block above each statement for
--          1:1 traceability.
--
-- IMPORTANT:
--   * These statements are demo prep, not production DDL/DML.
--   * Run order matters: 1 (duplicate check) -> 2 (insert) per record;
--     3 (count update), 4 (commit), then 5 (EOJ stats).
--   * Any non-zero SQLCODE on statements 2, 3, 4, or any of 5 must roll
--     back the current transaction (see 9999-ROLL-BACK at
--     source/procobol/LABD20.pco:489-529).
--   * All connection / authentication wiring (DBIO.pco USRID/PASSWD file
--     reads) must be replaced with a managed-secret config mechanism in
--     the modernized loader; see source/procobol/DBIO.pco:40-80.
-- =====================================================================

-- ---------------------------------------------------------------------
-- 0. Reference: TST123-COMMENT-REC fixed-width layout (file -> binds)
-- ---------------------------------------------------------------------
-- See source/procobol/LABD20.pco:43-55.
--
--   :submitted_key           CHAR(26)  -- TST123-LOAN-DT-NR  (bytes 1-26)
--                                       --   :comment_dt (PIC 9(8))     bytes  1- 8
--                                       --   :jv_number  (PIC 9(6))     bytes  9-14
--                                       --   :section_id (PIC 9(2))     bytes 15-16
--                                       --   :loan_number(PIC 9(10))    bytes 17-26
--   :schedule_doc_no         CHAR(10)  -- TST123-SCHEDULE-DOC-NO       (bytes 27- 36)
--   :comment_hist_240        CHAR(240) -- TST123-COMMENT-HIST          (bytes 27-266)
--   :comment_requestor       CHAR(20)  -- TST123-COMMENT-REQUESTOR     (bytes 267-286)
--   :comment_approver        CHAR(20)  -- TST123-COMMENT-APPROVER      (bytes 287-300, padded)
--   :control_num             CHAR(8)   -- :jv_number(6) || :section_id(2)
--   :updt_prog_id            CHAR(6)   -- literal 'LABD20'
--   :process_date_yyyymmdd   CHAR(8)   -- from CARDFILE (MM/DD/CCYY) -> CCYYMMDD
--   :jv_counter              NUMBER    -- WS-JV-COUNTER (PIC 9(12))
--   :prior_jv_counter        NUMBER    -- WS-JV-COUNTERS (PIC 9(12))
--
-- See analysis/field-lineage.md for the full lineage table.


-- =====================================================================
-- 1. Duplicate check (legacy DETERMINE-IF-DUPLICATE)
-- =====================================================================
-- Original embedded SQL:
--   EXEC SQL
--        SELECT JC_SUBMITTED_NUMBER
--          INTO :WS-CHECK-NUMBER
--          FROM JC_SUBMITTED_COMMENT_TBL
--         WHERE JC_SUBMITTED = :WS-TST123-LOAN-DT-NR
--   END-EXEC.
-- Source: source/procobol/LABD20.pco:317-339
--
-- Legacy host vars  -> demo bind vars:
--   :WS-CHECK-NUMBER        -> :existing_submitted_number  (NUMBER, OUT)
--   :WS-TST123-LOAN-DT-NR   -> :submitted_key              (CHAR(26))
--
-- SQLCODE semantics (preserved from legacy):
--   = 0    : duplicate found, log 'DUPLICATE ENTRY ...' and SKIP insert.
--   = 100  : not found, proceed to CREATE-COMMENT-RECORD (statement 2).
--   other  : route to 9999-ROLL-BACK.
-- ---------------------------------------------------------------------
SELECT JC_SUBMITTED_NUMBER
  INTO :existing_submitted_number
  FROM JC_SUBMITTED_COMMENT_TBL
 WHERE JC_SUBMITTED = :submitted_key;


-- =====================================================================
-- 2. Insert accepted comment (legacy CREATE-COMMENT-RECORD)
-- =====================================================================
-- Original embedded SQL:
--   EXEC SQL INSERT INTO JC_SUBMITTED_COMMENT_TBL
--            (JC_SUBMITTED,
--             JC_SUBMITTED_NUMBER,
--             JC_SUBMITTED_SCHED_DOC_NO,
--             JC_SUBMITTED_COMMENT_HIST,
--             JC_SUBMITTED_COMMENT_REQUESTOR,
--             JC_SUBMITTED_COMMENT_APPROVER,
--             JC_SUBMITTED_CONTROL_NUM,
--             JC_SUBMITTED_UPDT_PROG_ID,
--             JC_SUBMITTED_UPDT_PROG_DT)
--    VALUES   (:WS-TST123-LOAN-DT-NR,
--             :WS-JV-COUNTER,
--             :WS-TST123-SCHEDULE-DOC-NO,
--             :WS-TST123-COMMENT-HIST,
--             :WS-TST123-COMMENT-REQUESTOR,
--             :WS-TST123-COMMENT-APPROVER,
--             :WS-CONTROL-NUM,
--             'LABD20',
--             TO_DATE(:WS-PROCESS-DATE,'YYYYMMDD'))
--   END-EXEC.
-- Source: source/procobol/LABD20.pco:342-372
--
-- Legacy host vars  -> demo bind vars:
--   :WS-TST123-LOAN-DT-NR        -> :submitted_key
--   :WS-JV-COUNTER               -> :jv_counter            (NUMBER, IN)
--   :WS-TST123-SCHEDULE-DOC-NO   -> :schedule_doc_no
--   :WS-TST123-COMMENT-HIST      -> :comment_hist_240
--   :WS-TST123-COMMENT-REQUESTOR -> :comment_requestor
--   :WS-TST123-COMMENT-APPROVER  -> :comment_approver
--   :WS-CONTROL-NUM              -> :control_num
--   'LABD20'                     -> :updt_prog_id (default 'LABD20')
--   :WS-PROCESS-DATE             -> :process_date_yyyymmdd
--
-- Modernization recommendation: prefer MERGE / "INSERT ... WHERE NOT
-- EXISTS" so the duplicate detection and insert form a single
-- statement-level transaction; the two-statement legacy pattern is
-- vulnerable to a race window between statements 1 and 2.
-- ---------------------------------------------------------------------
INSERT INTO JC_SUBMITTED_COMMENT_TBL (
    JC_SUBMITTED,
    JC_SUBMITTED_NUMBER,
    JC_SUBMITTED_SCHED_DOC_NO,
    JC_SUBMITTED_COMMENT_HIST,
    JC_SUBMITTED_COMMENT_REQUESTOR,
    JC_SUBMITTED_COMMENT_APPROVER,
    JC_SUBMITTED_CONTROL_NUM,
    JC_SUBMITTED_UPDT_PROG_ID,
    JC_SUBMITTED_UPDT_PROG_DT
) VALUES (
    :submitted_key,
    :jv_counter,
    :schedule_doc_no,
    :comment_hist_240,
    :comment_requestor,
    :comment_approver,
    :control_num,
    :updt_prog_id,
    TO_DATE(:process_date_yyyymmdd, 'YYYYMMDD')
);


-- =====================================================================
-- 2b. Optional modernization: combined duplicate-check + insert
-- =====================================================================
-- This is NOT in the legacy code; it is a demo recommendation for
-- collapsing statements 1 and 2 into a single atomic operation.
-- It preserves the legacy semantics of "skip duplicates" and is what
-- the modernized Python loader should emit.
-- ---------------------------------------------------------------------
INSERT INTO JC_SUBMITTED_COMMENT_TBL (
    JC_SUBMITTED,
    JC_SUBMITTED_NUMBER,
    JC_SUBMITTED_SCHED_DOC_NO,
    JC_SUBMITTED_COMMENT_HIST,
    JC_SUBMITTED_COMMENT_REQUESTOR,
    JC_SUBMITTED_COMMENT_APPROVER,
    JC_SUBMITTED_CONTROL_NUM,
    JC_SUBMITTED_UPDT_PROG_ID,
    JC_SUBMITTED_UPDT_PROG_DT
)
SELECT
    :submitted_key,
    :jv_counter,
    :schedule_doc_no,
    :comment_hist_240,
    :comment_requestor,
    :comment_approver,
    :control_num,
    :updt_prog_id,
    TO_DATE(:process_date_yyyymmdd, 'YYYYMMDD')
  FROM DUAL
 WHERE NOT EXISTS (
        SELECT 1
          FROM JC_SUBMITTED_COMMENT_TBL
         WHERE JC_SUBMITTED = :submitted_key);


-- =====================================================================
-- 3. Section-count update (legacy POST-PROCESS)
-- =====================================================================
-- Original embedded SQL:
--   EXEC SQL UPDATE JC_COUNT_TBL
--      SET JC_SECTION_COUNT = :WS-JV-COUNTER
--      WHERE JC_SECTION = 'MA'
--   END-EXEC
-- Source: source/procobol/LABD20.pco:392-405
--
-- Guard condition in COBOL (must be evaluated before issuing this
-- statement): IF WS-JV-COUNTER > WS-JV-COUNTERS  (line 393).
-- The modernized loader should compute this in app code rather than in
-- SQL; an equivalent purely-SQL guard is shown below as an alternative.
-- ---------------------------------------------------------------------
UPDATE JC_COUNT_TBL
   SET JC_SECTION_COUNT = :jv_counter
 WHERE JC_SECTION = 'MA';

-- Optional purely-SQL guard (only updates when :jv_counter strictly
-- exceeds the persisted count). Equivalent to legacy IF WS-JV-COUNTER >
-- WS-JV-COUNTERS but executes atomically with the update:
UPDATE JC_COUNT_TBL
   SET JC_SECTION_COUNT = :jv_counter
 WHERE JC_SECTION = 'MA'
   AND :jv_counter > JC_SECTION_COUNT;


-- =====================================================================
-- 4. Commit (legacy CLOSE-SQL-ENVIRONMENT)
-- =====================================================================
-- Original embedded SQL:
--   EXEC SQL COMMIT WORK END-EXEC.
-- Source: source/procobol/LABD20.pco:408-416
-- ---------------------------------------------------------------------
COMMIT;


-- =====================================================================
-- 5. End-of-job stats (legacy CLOSE-SQL-ENVIRONMENT, continued)
-- =====================================================================
-- All three statements feed the EOJ report at
-- source/procobol/LABD20.pco:448-486. Any non-zero SQLCODE on any of
-- them routes to 9999-ROLL-BACK (lines 424-426, 434-436, 444-446).

-- 5.1 Submitted-table count
--   EXEC SQL SELECT COUNT(*) INTO :WS-TOTAL-SUBMIT-END-CNT
--      FROM JC_SUBMITTED_COMMENT_TBL END-EXEC.
-- Source: source/procobol/LABD20.pco:421-423
SELECT COUNT(*)
  INTO :total_submit_end_cnt
  FROM JC_SUBMITTED_COMMENT_TBL;

-- 5.2 Rejected-table count
--   EXEC SQL SELECT COUNT(*) INTO :WS-TOTAL-REJECT-END-CNT
--      FROM JC_REJECTED_COMMENT_TBL END-EXEC.
-- Source: source/procobol/LABD20.pco:431-433
SELECT COUNT(*)
  INTO :total_reject_end_cnt
  FROM JC_REJECTED_COMMENT_TBL;

-- 5.3 Applied-table count
--   EXEC SQL SELECT COUNT(*) INTO :WS-TOTAL-APPLIED-END-CNT
--      FROM JC_APPLIED_COMMENT_TBL END-EXEC.
-- Source: source/procobol/LABD20.pco:441-443
SELECT COUNT(*)
  INTO :total_applied_end_cnt
  FROM JC_APPLIED_COMMENT_TBL;


-- =====================================================================
-- 6. Rollback path (legacy 9999-ROLL-BACK)
-- =====================================================================
-- The legacy paragraph at source/procobol/LABD20.pco:489-529 does the
-- following on any unexpected SQL or DMS error:
--   1. Log the failing paragraph (WS-PARA-NAME), table (WS-TABLE-NAME),
--      command (WS-COMMAND-NAME), and SQLCODE.
--   2. Invoke RDMS-ERR-RTN (if SQL processing) or display DMS error
--      context (if DMS processing).
--   3. Call DBIO with DB-FUNCTION='ROLLBACK' / DB-FUNCTION-TYPE='DEPART',
--      which executes the SQL rollback shown below.
--   4. MOVE 99 TO RETURN-CODE and STOP RUN.
--
-- The actual SQL emitted by DBIO in that path (see
-- source/procobol/DBIO.pco:189-199) is:
--
--   EXEC SQL ROLLBACK END-EXEC.
--
-- Modernization recommendation: wrap the entire per-batch flow
-- (statements 1, 2, 3) in a single transaction context; on any
-- exception, ROLLBACK and exit non-zero. The 'DEPART' wrapper is a
-- legacy artifact and does not need a direct equivalent.
-- ---------------------------------------------------------------------
ROLLBACK;


-- =====================================================================
-- 7. Suggested execution sequence (modernized)
-- =====================================================================
-- 1. Open managed-config'd Oracle connection (no plaintext password file).
-- 2. Read process date from CARDFILE; convert MM/DD/CCYY -> CCYYMMDD.
-- 3. BEGIN TRANSACTION.
-- 4. For each comment record:
--      a. validate (see business-requirements/requirements-with-citations.md
--         section 2.3.2).
--      b. if invalid, increment reject counter and continue;
--      c. else execute statement 2b (combined dup-check + insert);
--         if 0 rows inserted, treat as duplicate (log and continue);
--         else increment :jv_counter.
-- 5. If final :jv_counter > prior persisted JC_COUNT_TBL.MA value,
--    execute statement 3 (purely-SQL guarded form).
-- 6. Execute statement 4 (COMMIT).
-- 7. Execute statements 5.1, 5.2, 5.3 (EOJ stats) for the report.
-- 8. On any error in steps 3-6: execute statement 6 (ROLLBACK), log
--    context, exit non-zero.

-- End of demo-extracted operations.
