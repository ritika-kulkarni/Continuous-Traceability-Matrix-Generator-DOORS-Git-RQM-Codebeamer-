# Requirement tags

Requirement tags are the **join key** across DOORS, Codebeamer, Git, and RQM.

## Format

Default regex (`app.req_tag_pattern`):

```text
REQ_[A-Z0-9]+(?:_[A-Z0-9]+)*_\d{3,}
```

| Part | Rule | Example |
|---|---|---|
| Prefix | Literal `REQ_` | `REQ_` |
| Segments | One or more uppercase alphanumeric groups separated by `_` | `ADAS_USS` |
| Sequence | At least 3 digits | `042` |

**Valid**

- `REQ_ADAS_USS_042`
- `REQ_BCM_PWR_001`
- `REQ_SYS_DIAG_1234`

**Invalid**

- `REQ_` (incomplete)
- `ADAS_USS_042` (missing prefix)
- `REQ-ADAS-USS-042` (hyphens)
- `REQ_ADAS_USS_42` (only 2 digits)

Matching is **case-insensitive** on input; values are normalized to **uppercase**.

## Where tags must appear

| Artifact | Where to put the tag |
|---|---|
| DOORS requirement | Official ID / attribute exported as `tag` |
| Codebeamer item | `requirementTags` field or title/description text |
| Git commit | Prefer header (below); body scan is fallback |
| Pull request | Title and/or body |
| RQM test case | `requirementTags` or name/description |

## Commit message convention (preferred)

```text
feat(uss): implement near-field ranging

Requires: REQ_ADAS_USS_042, REQ_ADAS_USS_043

Optional longer description…
```

Also accepted:

```text
REQ: REQ_ADAS_USS_042
```

When a `Requires:` / `REQ:` header is present, **only header tags** are used (body mentions are ignored). This avoids accidental linkage from discussion text.

If no header exists, the full message is scanned for tags.

## PR gate expectations

For each unique tag found in the PR:

1. Pattern must match  
2. Requirement must exist in DOORS  
3. At least one RQM **unit** or **integration** test case must be linked  

System/acceptance-only coverage is **not** sufficient for merge.

## Matrix join semantics

```text
Requirement.tag
    ← CodeItem.requirement_tags      (satisfies)
    ← GitCommit.requirement_tags     (implements)
    ← RqmTestCase.requirement_tags   (verifies)
         ← RqmExecution (latest status)
```

A row is **COMPLETE** only when design, commit, test case, and a non-failing/non-blocked execution are all present.

## Changing the pattern

1. Update `app.req_tag_pattern` in config  
2. Update this document and the PR template  
3. Re-run unit tests in `tests/unit/test_requirement_tag.py` (extend cases)  
4. Communicate the change to feature teams  

## Suggested PR template snippet

```markdown
## Requirements
- [ ] Commit messages include `Requires: REQ_...`
- [ ] Unit/integration test exists in RQM for each tag

Tags addressed: REQ_XXXX_YYY_000
```
