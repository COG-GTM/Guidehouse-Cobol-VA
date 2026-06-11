"""Root pytest configuration.

The three conversion-dataset slices intentionally share flat module names
(``mapper.py``, ``convert.py``, ``tests/test_conversion_slice.py``) so each
slice reads as a self-contained reference implementation. Collecting them in
one pytest process would cross-contaminate ``sys.path`` imports, so they are
excluded here and executed in isolated subprocesses by
``factory/tests/test_slice_suites.py`` instead. A plain ``pytest`` at the repo
root therefore runs every suite.
"""

collect_ignore_glob = ["factory/conversion-datasets/*"]
