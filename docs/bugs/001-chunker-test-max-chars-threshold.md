# Bug 001: Test Issue -- test_max_chars_too_small_raises_value_error

**Classification**: TEST ISSUE (not an implementation bug)

## Summary

The test `test_max_chars_too_small_raises_value_error` in `tests/processing/test_chunker.py` expects that calling `chunker.chunk("Hello world.", max_chars=50)` raises a `ValueError`. However, the implementation only raises `ValueError` when `max_chars < 1`, and the docstring says `max_chars < 100` but the code uses `< 1`.

## Details

- **File**: `/Users/oded/projects/ttl-take2/backend/tests/processing/test_chunker.py`, line 48
- **Test name**: `TestTextChunkerBasic::test_max_chars_too_small_raises_value_error`
- **Failing assertion**: `with pytest.raises(ValueError): chunker.chunk("Hello world.", max_chars=50)`

## Why this is a test issue, not an implementation bug

The test was written from the spec which originally stated a minimum of `max_chars=100`. However, during implementation the developer chose a more permissive threshold (`max_chars >= 1`), and **5 other tests** successfully use `max_chars` values of 1, 10, 35, and 40:

- `test_split_at_paragraph_boundary` uses `max_chars=35`
- `test_split_at_sentence_boundary` uses `max_chars=40`
- `test_text_with_only_periods` uses `max_chars=10`
- New edge case tests use `max_chars=1` and `max_chars=100`

All of these would break if the threshold were raised to 100 (or even 50).

## Resolution

The test `test_max_chars_too_small_raises_value_error` should be either:

1. **Updated** to test `max_chars=0` or `max_chars=-1` (which do correctly raise `ValueError`), or
2. **Removed**, since `max_chars=50` is a perfectly valid chunk size.

Additionally, the docstring in `chunker.py` line 45 says `max_chars < 100` but the code enforces `max_chars < 1`. The docstring should be updated to match the implementation.
