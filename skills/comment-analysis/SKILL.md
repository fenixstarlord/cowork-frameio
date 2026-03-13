---
name: comment-analysis
description: Analyze Frame.io comments, group feedback by reviewer and timecode, summarize themes, identify unresolved threads, extract action items
allowed-tools: frameio_list_comments, frameio_resolve_comment, frameio_get_file
---

# Comment Analysis

Fetch, parse, and analyze comments on Frame.io assets. This skill covers full pagination of comment threads, parsing timecode-anchored feedback, grouping comments by reviewer, summarizing feedback themes, identifying unresolved threads, and extracting actionable items.

## Prerequisites

- Authenticated Frame.io session (OAuth 2.0 via Adobe IMS)
- Account ID and file ID(s) for the assets to analyze
- For multi-asset analysis: use the `project-navigation` skill to identify target assets

## MCP Tools Used

| Tool | Purpose |
|------|---------|
| `frameio_list_comments` | Fetch comments on a file (paginated) |
| `frameio_create_comment` | Add a new comment to a file |
| `frameio_resolve_comment` | Mark a comment as resolved |

---

## Capability 1: Fetch All Comments

### Overview

Comments in Frame.io are attached to individual files. Each comment may include a timecode (anchoring it to a specific frame in video) and a resolved/unresolved status. The API paginates results, so you must follow cursor links to retrieve all comments on heavily-reviewed assets.

### Step-by-Step

1. **Fetch the first page of comments.**
   Call `frameio_list_comments` with:
   - `asset_id`: the file ID
   - Request page size of 100 (maximum) for efficiency.

2. **Paginate to collect all comments.**
   The tool uses cursor-based pagination. Continue calling `frameio_list_comments` following the next cursor until all comments are retrieved.
   - For assets with hundreds of comments, this may require multiple pages.
   - Collect all comments into a single list before analysis.

3. **Sort comments.**
   Useful sort orders:
   - `created_at_asc`: chronological order (default for analysis)
   - `timecode_asc`: order by position in the video timeline (experimental, useful for edit-driven reviews)

4. **Comment fields to extract.**
   For each comment, capture:
   - `id`: unique identifier
   - `text`: the comment body
   - `timecode`: the frame/time reference (may be null for general comments)
   - `creator_id`: who wrote it
   - `created_at`: when it was posted
   - `resolved`: boolean indicating if the thread is closed

---

## Capability 2: Group Comments by Reviewer

### Overview

Organize comments by who said them, giving each reviewer's feedback as a coherent block. This helps editors and producers understand each stakeholder's perspective.

### Step-by-Step

1. **Collect all comments** using Capability 1.

2. **Group by `creator_id`.**
   Create a map: `creator_id -> [list of comments]`.

3. **Resolve reviewer identities.**
   The `creator_id` is a user ID. If the user's name is available in comment metadata or can be resolved through account context, use names instead of IDs for readability.

4. **Present per-reviewer summaries.**
   For each reviewer:
   - Total number of comments
   - Number of unresolved comments
   - List of comments with timecodes (if applicable)
   - Key themes or repeated feedback

5. **Format output.**
   ```
   ## Reviewer: [Name or ID]
   - Comments: 12 (4 unresolved)
   - Key feedback:
     - [TC 00:01:23:15] "The opening shot needs more contrast"
     - [TC 00:03:45:00] "Music transition is too abrupt"
     - [General] "Overall pacing feels rushed in the first act"
   ```

---

## Capability 3: Parse Timecode-Anchored Comments

### Overview

Video-specific comments include a `timecode` field that anchors feedback to a specific frame. Parsing these allows you to create a timeline-ordered view of all feedback, which is essential for editors.

### Step-by-Step

1. **Collect all comments** using Capability 1.

2. **Separate timecoded vs. general comments.**
   - Timecoded: `timecode` field is not null
   - General: `timecode` is null (applies to the asset as a whole)

3. **Sort timecoded comments by timecode.**
   Parse timecodes (format: `HH:MM:SS:FF` where FF is frames) and sort chronologically.

4. **Group by timecode proximity.**
   Comments within a few seconds of each other likely relate to the same moment. Group them:
   - Define a proximity window (e.g., 5 seconds)
   - Cluster comments whose timecodes fall within the window
   - Label each cluster by its timecode range

5. **Present timeline view.**
   ```
   ## Timeline Feedback

   ### 00:01:20 - 00:01:25 (3 comments)
   - [Reviewer A] "Opening shot needs more contrast"
   - [Reviewer B] "Agree, also the framing is too tight"
   - [Reviewer C] "Color looks fine to me" (RESOLVED)

   ### 00:03:45 (1 comment)
   - [Reviewer A] "Music transition is too abrupt"

   ### General Comments (no timecode)
   - [Reviewer B] "Overall pacing feels good"
   ```

---

## Capability 4: Summarize Feedback Themes

### Overview

Synthesize comments into high-level themes. This helps decision-makers understand the consensus without reading every individual comment.

### Step-by-Step

1. **Collect all comments** using Capability 1.

2. **Identify recurring themes.**
   Analyze comment text for common topics. Typical categories in video review:
   - **Visual**: color grading, framing, lighting, exposure
   - **Audio**: music, sound effects, dialogue, mixing levels
   - **Pacing/Editing**: cut timing, transitions, flow, duration
   - **Content**: storytelling, messaging, branding, text/graphics
   - **Technical**: resolution, codec, artifacts, sync issues

3. **Classify each comment.**
   Assign one or more theme labels to each comment based on its content.

4. **Detect consensus vs. disagreements.**
   - **Consensus**: multiple reviewers flag the same issue or give the same feedback.
   - **Disagreement**: reviewers contradict each other on the same topic.
   - Flag disagreements clearly so the decision-maker can resolve them.

5. **Present theme summary.**
   ```
   ## Feedback Themes

   ### Color Grading (5 comments, 3 reviewers)
   - Consensus: Opening sequence needs warmer tones
   - Disagreement: Reviewer A wants cooler midtones, Reviewer C says current grade is fine

   ### Audio / Music (3 comments, 2 reviewers)
   - Consensus: Transition at 03:45 is too abrupt
   - Action needed: Source alternative music bed for bridge section

   ### Pacing (2 comments, 2 reviewers)
   - Consensus: First act feels rushed
   ```

---

## Capability 5: Identify Unresolved Threads

### Overview

Find all comments that have not been resolved, representing open feedback that still needs to be addressed.

### Step-by-Step

1. **Collect all comments** using Capability 1.

2. **Filter to unresolved.**
   Select comments where `resolved` is `false`.

3. **Prioritize.**
   Order unresolved comments by:
   - Timecode (if present) — address in video order
   - Creation date — oldest unresolved first
   - Reviewer — group by who raised the issue

4. **Present unresolved list.**
   ```
   ## Unresolved Feedback (7 items)

   1. [TC 00:01:23] Reviewer A: "Opening shot needs more contrast"
   2. [TC 00:03:45] Reviewer A: "Music transition is too abrupt"
   3. [TC 00:05:12] Reviewer B: "Lower third is misaligned"
   4. [General] Reviewer C: "Need to add end card with legal copy"
   ...
   ```

5. **Resolve comments when addressed.**
   After an issue is fixed, call `frameio_resolve_comment` with the comment ID to mark it as resolved. Confirm with the user before resolving.

---

## Capability 6: Extract Action Items

### Overview

Convert feedback into a structured list of action items that the editor or team can work through.

### Step-by-Step

1. **Analyze all unresolved comments** (Capability 5).

2. **Extract actionable directives.**
   Look for comments that imply specific changes:
   - "Needs to be..." / "Should be..." / "Change the..."  -> direct action
   - "I think..." / "Maybe..." -> suggestion (flag as optional)
   - "Love this" / "Great work" -> positive feedback (not an action item)

3. **Structure each action item.**
   - **What**: the change to make
   - **Where**: timecode or general location
   - **Who requested**: reviewer name/ID
   - **Priority**: based on consensus (multiple reviewers = higher priority)

4. **Present action list.**
   ```
   ## Action Items

   ### High Priority (multiple reviewers agree)
   - [ ] [TC 00:01:23] Increase contrast in opening shot (Reviewer A, B)
   - [ ] [TC 00:03:45] Smooth music transition at bridge (Reviewer A, B)

   ### Standard
   - [ ] [TC 00:05:12] Realign lower third graphic (Reviewer B)
   - [ ] [General] Add end card with legal copy (Reviewer C)

   ### Suggestions (optional)
   - [ ] [TC 00:02:00] Consider tighter crop on interview (Reviewer C)
   ```

---

## Multi-Asset Analysis

When analyzing comments across multiple assets (e.g., all files in a review folder):

1. Use `frameio_list_folder` to get all file IDs in the target folder.
2. Fetch comments for each file using Capability 1.
3. Aggregate results across all files.
4. In the output, clearly label which file each comment belongs to.
5. Be mindful of rate limits when fetching comments for many files in sequence.

---

## Error Handling

### Authentication Errors (401)
Token expired or invalid. Trigger token refresh. If refresh fails, prompt user to re-authenticate.

### No Comments Found
If `frameio_list_comments` returns an empty result:
- Verify the asset ID is correct.
- Confirm the asset has been shared and reviewed (comments only exist if someone has posted them).
- Report to the user that no comments were found on the specified asset.

### Permission Errors (403)
The user may not have permission to view comments on certain assets. This can happen with restricted projects. Report which assets are inaccessible.

### Pagination Failures
If pagination stops unexpectedly (API error mid-pagination):
- Report how many comments were successfully fetched.
- Note that the analysis may be incomplete.
- Offer to retry fetching the remaining pages.

### Rate Limiting (429)
Fetching comments across many assets may trigger rate limits. The MCP server handles backoff automatically. For large-scale analysis:
- Process one asset at a time.
- Report progress to the user during long operations.

### Invalid Asset ID (404)
The file ID does not exist or has been deleted. Verify the ID and check if the file was recently removed.

### Comment Resolution Failures
If `frameio_resolve_comment` fails:
- `403`: the user may not have permission to resolve comments on this asset.
- `404`: the comment may have been deleted.
- Report the specific error and skip the failed comment, continuing with others.
