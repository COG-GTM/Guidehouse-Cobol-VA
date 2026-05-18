# Guidehouse Open Questions

Extracted from `/Users/jakecosme/Downloads/Cognition Open Questions.xlsx`. The workbook did not include completed answers in the answer column.

## Response Themes For Demo Prep

- Show post-modernization documentation generation, not only legacy documentation.
- Demonstrate handling of COBOL data definitions, fixed-width files, indexed/record sequential files, copybooks, embedded SQL, Perl, sqlplus, and sqlldr as part of a system graph.
- Show system-wide dependencies and field-level lineage where source context permits, while marking dynamic calls and missing artifacts with confidence levels.
- Demonstrate generated requirements, conversion output, tests, and review loops rather than claiming fully unsupervised migration.
- Confirm deployment/security/compliance wording with federal GTM/security before customer delivery.

## Questions

| # | Owner | Question | Prep Notes |
| --- | --- | --- | --- |
| 1 | Jill | The tools create a lot of documentation based on the COBOL programs and jobs, but that documentation will not be effective after the conversion/modernization. Can the tools create new documentation after the modernization is complete? | Prepare a before/after doc-generation example from `LABD20` and the converted Python/SQL. |
| 2 | Jill | How do the conversion agents handle COBOL-specific data field definitions such as COMP, COMP-X, and BINARY? | Show parser reasoning for PIC/USAGE/BINARY fields, including `CONTROL-RECORD-TABLE-IO.pco` binary mapping. |
| 3 | Jill | How does the tool handle different file types such as record sequential (as opposed to line sequential), indexed, and variable length? | Discuss line sequential in supplied files and approach for record sequential, indexed, and variable-length files. |
| 4 | Jill | Does the tool understand Perl scripts, sqlplus, and sqlldr? | Show `source/perl/` wrappers and describe multi-language ingestion/dependency handling. |
| 5 | Jill | How much labor will be required from COBOL developers to ensure accurate output from the tool? | Position as expert-in-the-loop: Devin accelerates analysis/conversion, COBOL SMEs review edge cases and acceptance tests. |
| 7 | Sunil | We saw the general set up and confluence page but need to see demo of a. code conversion to Python and/or Oracle SQL b. Formal Functional requirement generation c. Data Flow and Dependency diagaram d. Test plans, scenarios and scripts e. a view of code conversion efficiency | Use `docs/demo-plan.md` agenda and generate tests from `business-requirements/initial-requirements.md`. |
| 8 | Jill | Can the tool convert COBOL to Oracle SQL? | Extract embedded SQL from `LABD20.pco` and CRUD from `CONTROL-RECORD-TABLE-IO.pco`. |
| 9 | Srinjoy | Can your system resolve dependencies across copybooks, includes, and dynamically referenced components (e.g., conditional includes, runtime program calls)? | Use `analysis/dependency-map.md`; identify missing `DATECONV-*` copybooks and DBIO dispatch. |
| 10 | Srinjoy | Does this tool construct a complete system-wide dependency graph (programs, copybooks, jobs) in the backend, or is analysis performed at an individual file level? | Use `analysis/dependency-map.md`; identify missing `DATECONV-*` copybooks and DBIO dispatch. |
| 11 | Srinjoy | Do you construct a data flow graph with field-level lineage across programs and files, or only a call graph of program interactions? | Trace `TST123-COMMENT-REC` fields into `JC_SUBMITTED_COMMENT_TBL` columns. |
| 12 | Charles | How do you handle dynamically constructed program calls (e.g., CALL using variables)? Do you resolve these via static analysis, heuristics, or runtime tracing? | Discuss static analysis plus heuristics/runtime evidence for dynamic calls; this source has explicit DBIO dispatch. |
| 13 | Charles | Do you build an intermediate representation or canonical system model before generating outputs (documentation, diagrams, converted code, etc.), or are outputs generated directly from source parsing? | Frame repo-level model as programs, copybooks, files, tables, SQL ops, fields, and requirements. |
| 14 | Charles | Can you trace data lineage end-to-end across COBOL programs, batch jobs, and underlying data stores? | Trace `TST123-COMMENT-REC` fields into `JC_SUBMITTED_COMMENT_TBL` columns. |
| 15 | Charles | How do you measure and/or expose confidence in dependency and data flow analysis results? | Show confidence based on resolved dependencies, source citations, and missing-artifact flags. |
| 16 | Margarita | What constructs are not supported or require manual remediation? | List unsupported/needs-review constructs; mark missing copybooks and runtime-only behavior. |
| 17 | Margarita | Can the tool reverse-engineer COBOL to generate test scenarios and test cases? | Generate validation, duplicate, insert, count-update, and rollback test scenarios. |
| 18 | Margarita | Where does the tool execute (vendor cloud vs client-managed environment)? Can it run fully within a client AWS environment without code leaving the boundary? | Use approved federal deployment/security talk track; do not improvise final compliance answers. |
| 19 | Margarita | How is source code and data secured during processing? | Use approved federal deployment/security talk track; do not improvise final compliance answers. |
| 20 | Margarita | What is the current FedRAMP authorization status and timeline for FedRAMP High? | Use approved federal deployment/security talk track; do not improvise final compliance answers. |
| 21 | Margarita | Please confirm the full list of supported target languages and maturity level for each. | Confirm supported-language maturity matrix with product/GTM before final answer. |
| 22 | Margarita | How are agents orchestrated during conversion workflows? Can users inspect or influence agent decision-making steps? | Show inspectable task plan, source citations, diffs, tests, and user review checkpoints. |

## By Owner

### Charles

- 12: How do you handle dynamically constructed program calls (e.g., CALL using variables)? Do you resolve these via static analysis, heuristics, or runtime tracing?
- 13: Do you build an intermediate representation or canonical system model before generating outputs (documentation, diagrams, converted code, etc.), or are outputs generated directly from source parsing?
- 14: Can you trace data lineage end-to-end across COBOL programs, batch jobs, and underlying data stores?
- 15: How do you measure and/or expose confidence in dependency and data flow analysis results?

### Jill

- 1: The tools create a lot of documentation based on the COBOL programs and jobs, but that documentation will not be effective after the conversion/modernization. Can the tools create new documentation after the modernization is complete?
- 2: How do the conversion agents handle COBOL-specific data field definitions such as COMP, COMP-X, and BINARY?
- 3: How does the tool handle different file types such as record sequential (as opposed to line sequential), indexed, and variable length?
- 4: Does the tool understand Perl scripts, sqlplus, and sqlldr?
- 5: How much labor will be required from COBOL developers to ensure accurate output from the tool?
- 8: Can the tool convert COBOL to Oracle SQL?

### Margarita

- 16: What constructs are not supported or require manual remediation?
- 17: Can the tool reverse-engineer COBOL to generate test scenarios and test cases?
- 18: Where does the tool execute (vendor cloud vs client-managed environment)? Can it run fully within a client AWS environment without code leaving the boundary?
- 19: How is source code and data secured during processing?
- 20: What is the current FedRAMP authorization status and timeline for FedRAMP High?
- 21: Please confirm the full list of supported target languages and maturity level for each.
- 22: How are agents orchestrated during conversion workflows? Can users inspect or influence agent decision-making steps?

### Srinjoy

- 9: Can your system resolve dependencies across copybooks, includes, and dynamically referenced components (e.g., conditional includes, runtime program calls)?
- 10: Does this tool construct a complete system-wide dependency graph (programs, copybooks, jobs) in the backend, or is analysis performed at an individual file level?
- 11: Do you construct a data flow graph with field-level lineage across programs and files, or only a call graph of program interactions?

### Sunil

- 7: We saw the general set up and confluence page but need to see demo of a. code conversion to Python and/or Oracle SQL b. Formal Functional requirement generation c. Data Flow and Dependency diagaram d. Test plans, scenarios and scripts e. a view of code conversion efficiency
