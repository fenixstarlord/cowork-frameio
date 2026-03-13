---
description: "Gather and summarize all comments on a Frame.io asset. Groups feedback by reviewer and timecode, synthesizes themes, and extracts action items."
---

# /frameio:collect-feedback

Collect all comments on a Frame.io asset, organize them by reviewer and timecode, and produce a structured summary with themes and action items.

## Inputs

| Input | Source | Required | Description |
|-------|--------|----------|-------------|
| Asset | User prompt | Yes | The asset to collect feedback for. Can be an asset ID, asset name, or a path like `Project / Folder / filename.mp4`. |
| Project | User prompt or `frameio.local.md` default | Conditional | Required if the asset is specified by name or path rather than by ID. |
| Include resolved | User prompt | No | Whether to include already-resolved comments. Defaults to `false` (only unresolved). |
| Output format | User prompt | No | `summary` (default) or `full`. Summary mode groups and synthesizes; full mode lists every comment verbatim. |

If the user does not specify an asset, prompt for one. If they give a name without a project context, ask which project to search in.

## Workflow

1. **Authenticate.**
   - Call `frameio_whoami` to verify the session. Handle auth failure per **Auth Handling** below.

2. **Resolve the asset.**
   - If the user provided an asset ID, call `frameio_get_file` to confirm it exists.
   - If the user provided a name or path:
     - Resolve the project (from input or `frameio.local.md` default).
     - Navigate the folder tree using `frameio_list_folder`, starting from the project's `root_folder_id`.
     - Match the asset by name (case-insensitive). If multiple matches, present options.

3. **Fetch all comments.**
   - Call `frameio_list_comments` for the asset ID.
   - Paginate fully — follow `links.next` until all comments are retrieved.
   - If `include_resolved` is false, filter out comments with `resolved_at` set.

4. **Parse comment data.**
   For each comment, extract:
   - `id`, `text`, `author` (name + email)
   - `timestamp` (timecode anchor, if present — format as `HH:MM:SS:FF`)
   - `created_at`
   - `resolved_at` (null if unresolved)
   - `parent_id` (for threaded replies)

5. **Group comments.**
   - **By reviewer:** Group all comments by author name.
   - **By timecode:** For timecode-anchored comments, sort by timecode and group into timecode ranges (e.g., 00:00:00–00:00:30, 00:00:30–00:01:00).
   - **Threads:** Nest replies under their parent comments.

6. **Delegate synthesis to feedback-synthesizer.**
   - Pass the grouped comment data to the **feedback-synthesizer** sub-agent.
   - The feedback-synthesizer will:
     - Identify recurring themes across reviewers.
     - Flag areas of consensus and disagreement.
     - Extract concrete action items with associated timecodes.
     - Highlight unresolved threads that need attention.

7. **Present the report.**
   - Combine the structured groupings with the synthesized analysis.
   - Format according to the requested output format (summary or full).

## Expected Output

**Summary mode (default):**
```
Feedback Summary for "hero_v3.mp4"
===================================
12 comments from 3 reviewers | 5 unresolved | 4 action items

Themes:
  1. Color grading too warm in outdoor scenes (3 reviewers agree)
  2. Audio mix needs rebalancing at transitions (2 reviewers)
  3. End card timing feels rushed (1 reviewer)

Action Items:
  [ ] Cool down color grade in outdoor scenes — 00:00:45–00:01:12
  [ ] Lower music bed at dialogue transitions — 00:01:30, 00:02:15
  [ ] Extend end card hold by 1-2 seconds — 00:03:28
  [ ] Address continuity note at 00:02:05 (reviewer: Jane D.)

By Reviewer:
  Sarah M. (5 comments, 2 unresolved)
    - 00:00:45 — "The color grading feels too warm here..."
    - 00:01:30 — "Music is overpowering the VO at this transition"
    - 00:02:05 — "Love this shot, great improvement from v2" (resolved)
    ...

  Jane D. (4 comments, 2 unresolved)
    ...

  Tom R. (3 comments, 1 unresolved)
    ...

Unresolved Threads:
  - Thread at 00:00:45 (2 replies, started by Sarah M.)
  - Thread at 00:02:05 (1 reply, started by Jane D.)
```

**Full mode:**
All comments listed verbatim, organized by timecode, with reviewer attribution and thread nesting.

**No comments found:**
```
No comments found on "hero_v3.mp4".
This asset has not received any feedback yet.
```

## Auth Handling

- Before any API call, verify authentication by calling `frameio_whoami`.
- If the call returns an authentication error (401 or token-missing):
  1. Inform the user: "You are not authenticated with Frame.io. Starting OAuth login..."
  2. The MCP server's auth module will initiate the Adobe IMS OAuth 2.0 flow.
  3. Guide the user through any required browser-based steps.
  4. Once tokens are obtained, retry the original request.
- If token refresh fails, surface the error and ask the user to re-authenticate.

## Delegation

| Condition | Delegate To | Reason |
|-----------|-------------|--------|
| Always (for summary mode) | **feedback-synthesizer** | Theme identification, consensus detection, and action item extraction require analytical processing that the feedback-synthesizer agent is purpose-built for. |

In **full mode**, the command can skip the feedback-synthesizer and present raw grouped comments directly, though the synthesizer is still used if the user requests action items or themes alongside the full listing.
