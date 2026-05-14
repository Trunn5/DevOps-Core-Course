# Cloudflare Workers Edge API

Edge-deployed serverless API for DevOps Core Course Lab 17.

## Project Structure

```
edge-api/
├── src/
│   └── index.ts         # Worker source code
├── wrangler.jsonc       # Cloudflare Workers config
├── package.json         # Dependencies and scripts
├── tsconfig.json        # TypeScript config
└── README.md           # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
cd edge-api
npm install
```

### 2. Authenticate with Cloudflare

```bash
npx wrangler login
npx wrangler whoami
```

### 3. Configure Secrets

```bash
npx wrangler secret put API_TOKEN
npx wrangler secret put ADMIN_EMAIL
```

### 4. Create KV Namespace

```bash
npx wrangler kv namespace create SETTINGS
```

Copy the returned namespace ID and add it to `wrangler.jsonc`:

```jsonc
"kv_namespaces": [
  {
    "binding": "SETTINGS",
    "id": "your-namespace-id-here"
  }
]
```

## Development

### Run Locally

```bash
npm run dev
```

Access at: `http://localhost:8787`

### Deploy to Production

```bash
npm run deploy
```

Your Worker will be available at: `https://edge-api.<your-subdomain>.workers.dev`

## API Endpoints

- `GET /` - API information and available endpoints
- `GET /health` - Health check endpoint
- `GET /edge` - Edge metadata (colo, country, city, ASN, protocol)
- `GET /counter` - KV-backed visit counter (persistence demo)
- `GET /config` - Show configuration and secrets status

## Operations

### View Logs

```bash
npm run tail
```

### View Deployments

```bash
npm run deployments
```

### Rollback to Previous Version

```bash
npm run rollback
```

## Configuration

### Environment Variables (Plaintext)

Defined in `wrangler.jsonc`:
- `APP_NAME` - Application name
- `COURSE_NAME` - Course identifier
- `VERSION` - Application version

### Secrets (Encrypted)

Set via CLI (never committed to Git):
- `API_TOKEN` - Example API token
- `ADMIN_EMAIL` - Example admin email

### Workers KV

- `SETTINGS` - Key-value namespace for persistent state
  - `visits` - Visit counter
  - `last_visit` - Last visit timestamp

## Resources

- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/)
- [Workers KV](https://developers.cloudflare.com/kv/)
- [Workers Runtime APIs](https://developers.cloudflare.com/workers/runtime-apis/)
