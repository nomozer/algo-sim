# Frozen oracle sources

Byte-exact copies of the oracle files that `frontend/scripts/generic-tier-a-scenarios.json` pins by the SHA-256 of their
git blob (`oracle_source.sha256`, `hash_basis = git_blob_at_measurement_commit`). The originals —
`backend/tests/geometry/test_prism_production_route.py`, `test_rectangular_pyramid_production_route.py` and
`test_cuboid_cube_production_route.py` — were deleted by main's Hybrid cutover `52205f45` (they exercised the retired
LLM_ONLY route), which left two `frontend/scripts/compiler-scene-replay-lib.node-test.mjs` tests failing on
`git show HEAD:<path>`.

Each file here is `git show 52205f45^:<original path>`, unchanged; only the manifest `path` moved. The SHA-256 pins were
not touched and still verify, so a change to any hand-authored oracle (`_pyramid_control_contract`, `_prism_p01_contract`,
`_rect_pyramid_contract`, `_cuboid_p01_payload`, `_cube_p01_payload`) is still detected. Stored as `.py.txt` so no test
runner collects them: they document the oracle, they do not test the current route.
