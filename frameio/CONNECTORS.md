# Frame.io Connector Setup

## Prerequisites

- An Adobe ID with access to [Adobe Developer Console](https://developer.adobe.com/console)
- A Frame.io account with V4 API access
- Admin or Developer role on the Frame.io account

## Step 1: Create an Adobe Developer Console Project

1. Go to [Adobe Developer Console](https://developer.adobe.com/console)
2. Click **Create new project**
3. Name it (e.g., "Cowork Frame.io Plugin")

## Step 2: Add Frame.io API

1. In your project, click **Add API**
2. Select **Frame.io API** from the list
3. Click **Next**

## Step 3: Create OAuth Web App Credential

1. Select **OAuth Web App** as the credential type
2. Set the **Redirect URI** to `http://localhost:9876/callback`
3. Add the required scopes: `openid`, `AdobeID`, `frameio.apps.readwrite`
4. Click **Save configured API**
5. Note your **Client ID** and **Client Secret**

## Step 4: Configure Environment Variables

Add your credentials to the `.mcp.json` file in the plugin root:

```json
{
  "mcpServers": {
    "frameio": {
      "type": "stdio",
      "command": "bash",
      "args": ["mcp-server/setup.sh"],
      "env": {
        "FRAMEIO_CLIENT_ID": "<your-client-id>",
        "FRAMEIO_CLIENT_SECRET": "<your-client-secret>"
      }
    }
  }
}
```

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `FRAMEIO_CLIENT_ID` | Yes | OAuth client ID from Adobe Developer Console |
| `FRAMEIO_CLIENT_SECRET` | Yes | OAuth client secret |
| `FRAMEIO_ACCOUNT_ID` | No | Default account ID (avoids prompting) |
| `FRAMEIO_TOKEN_PATH` | No | Token storage path (default: `~/.frameio/tokens.json`) |

## Step 5: Authenticate

On first use, the plugin will:
1. Open a browser window for Adobe IMS login
2. You authenticate with your Adobe ID
3. Grant Frame.io access to the plugin
4. Tokens are stored at `~/.frameio/tokens.json`
5. Tokens refresh automatically (24h expiry)

## Security Notes

- Never commit `.mcp.json` with real credentials to version control
- Token files at `~/.frameio/tokens.json` contain sensitive data
- The plugin never logs or displays OAuth tokens
