# Changelog

All notable changes to this project should be documented in this file.

## [Unreleased] - 2025-09-22

### Fixed
- Fix FieldError on user profile dashboard caused by queries using a non-existent model field `booking_date`. Query filters and ordering now use `start_date` and `start_time` (actual DB fields) in code paths that build QuerySets.

### Added
- Backwards-compatibility properties on `bookings.models.Booking`:
  - `booking_date` -> alias for `start_date`
  - `booking_time` -> alias for `start_time`
  These preserve template and code attribute access for legacy callers while allowing QuerySet filters to use the real DB fields.

### Tests
- Ran full Django test suite (46 tests). Initially three tests failed due to a missing test dependency (`beautifulsoup4`), which was installed. Final test run: all tests passed (46/46).

### Notes & Next steps
- Search/monitor for any remaining usage that attempts QuerySet lookups using `booking_date__*` — properties won't make `booking_date` usable in lookups. Updated identified files include `accounts/profile_views.py`, `admin_dashboard/views.py`, and `api/auth.py`.
- When debugging is finished, revert staging `DEBUG` to False and restart the systemd unit.
