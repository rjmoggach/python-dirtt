# dirtt migrate — Template-to-Template Migration Design

**Status:** approved in discussion 2026-08-18; awaiting spec review.
**Target release:** v1.1.0 (pure addition, nothing breaking).

## Problem

A tree on disk was built from template A (e.g. `studio_project_2015/project.xml`).
Template B (`studio_project_2026/project.xml`) is the new layout. Today the only
option is manual `mv`. dirtt should compute and apply the difference: what moves,
what gets created, what is orphaned — safely, with a dry-run default.

## CLI

```
dirtt migrate PATH --from OLD_TEMPLATE --to NEW_TEMPLATE
              [--map MAP.json] [--var K=V ...] [--apply] [--prune]
```

- `PATH` — the existing tree root on disk (the directory that corresponds to
  the old template's root).
- Default is **dry-run**: print the full plan, touch nothing. `--apply` executes.
  (Deliberately opposite to `create`, because migrate moves real data.)
- `--map MAP.json` — flat JSON object, `"old key": "new key"`.
- `--var` — same context vars used to render both templates.
- `--prune` — additionally remove orphaned directories **that are empty** after
  all moves. Never anything with content.

## Matching (how a node in A pairs with a node in B)

In priority order; first match wins, each node matches at most once:

1. **Same `id`** in both templates.
2. **Explicit map entry.** Keys and values may each be a template `id` or a
   root-relative path (`"work/_DAILIES": "work/dailies"`). Paths use the
   rendered (post-substitution) names.
3. **Identical root-relative path** — unchanged nodes need no mapping.

Unmatched in B → **create**. Unmatched in A → **orphan** (keep + report).

A map entry whose key matches nothing in A, or whose value matches nothing in
B, is an error before anything runs (catches typos).

Mapping a parent dir moves its whole subtree; a child with its own id/map
entry/path match is re-parented according to its own match instead.

## Planning

Order of the produced plan:

1. **Moves** for matched pairs whose path changed — planned top-most first;
   descendant paths are recomputed after each ancestor's move so nested
   renames compose. If a move's target lies inside another pending move's
   source (swaps, overlaps), it stages through `.__dirtt_tmp_<n>` in the tree
   root, with the un-staging move appended after the conflicting move.
2. **Creates** (`mkdir`/`write`) for only-in-B nodes — reuses the existing
   builder actions. Links from template B are (re)planned last, as in `create`;
   an existing correct symlink is left alone, an existing wrong one is an error.
3. **Orphan report** for only-in-A nodes — informational lines, no actions,
   except `--prune` which appends `rmdir` actions for orphan dirs that are
   empty once moves complete.

Permissions: migrate does not chmod/chown matched nodes (their content is the
user's); created nodes get template B's perms as usual.

## Validation (before apply, all findings listed at once)

- Every move source must exist on disk; missing → **warn + skip** (the disk is
  the truth, template A only declares intent).
- No two moves may share a target; no move target may already exist on disk
  (unless it is the staged-temp flow). Violations → error, nothing executed.
- `PATH` must exist and be a directory.

## Execution semantics

- New `Action` ops: `"move"` (`Path` → `target` path) and `"rmdir"` (prune
  only, `os.rmdir`, fails on non-empty → reported, not fatal).
- A dir move is one `os.rename` (same filesystem assumed; cross-device falls
  back to error, not copy — v1 does not copy data). User files inside a moved
  dir travel with it, never touched individually.
- Failure mid-apply stops, reports completed actions. Re-running is safe:
  completed moves now auto-match by path (rule 3) and produce no new actions —
  migrate is idempotent.
- Nothing ever deletes file content. `--prune` removes empty dirs only.

## Code shape

- `dirtt/migrate.py` — `match(tree_old, tree_new, mapping) -> Matches`,
  `diff(matches, root: Path, *, prune: bool) -> list[Action]` (includes
  validation), ~200 lines.
- `dirtt/model.py` — extend `Action.op` literal with `"move"`/`"rmdir"`;
  `describe()` covers both.
- `dirtt/builder.py` — `execute()` handles the two new ops.
- `dirtt/cli.py` — `migrate` subcommand.
- `tests/test_migrate.py` — pytest, all in `tmp_path`.

## Testing

Unit: pure rename; deep restructure via map file; nested parent+child rename;
swap (a→b, b→a) through temp staging; orphan with user data untouched;
missing-source warn+skip; target-collision error; bad map key/value error;
prune removes only empty orphans; dry-run touches nothing; re-run is a no-op.

Acceptance (real corpus): build `studio_project_2015/project.xml` into
`tmp_path`, drop a user file into `work/_DAILIES`, migrate with
`migrations/2015_to_2026.json` to `studio_project_2026/project.xml`, assert
the user file lands in `work/dailies`, `library` became `assets`,
`production/online` became `editorial`, orphans reported, second run plans
zero moves.

## Out of scope (v1)

Cross-filesystem copies; merging two source dirs into one target (map values
must be unique); file-content transformation; chmod of matched nodes; undo.
