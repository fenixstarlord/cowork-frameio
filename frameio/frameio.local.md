# Frame.io Local Configuration

## Account Settings

- **account_id**: `<YOUR_ACCOUNT_ID>`
- **workspace_id**: `<YOUR_WORKSPACE_ID>`
- **default_project_id**: `<YOUR_DEFAULT_PROJECT_ID>`

## Custom Fields

Define your project's custom field schema below. The plugin uses these
for approval gates, filtering, and review workflows.

- Review Status: `Pending` | `In Review` | `Approved` | `Needs Revision` | `Final`
- Shot Type: `Wide` | `Medium` | `Close-Up` | `Insert` | `VFX`
- Delivery Tier: `Hero` | `Secondary` | `BTS` | `Archive`

## Approval Criteria

- Approval requires: Review Status = `Approved` AND Rating >= 4

## Preferences

- Default share access level: `private`
- Default share expiration: 7 days
- Upload chunk concurrency: 4
