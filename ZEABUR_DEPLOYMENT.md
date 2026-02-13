# AgentLink - Zeabur Deployment Configuration

## Deployment Overview

AgentLink Relay Server is deployed to Zeabur with the following components:

- **FastAPI Application** (Python 3.11+)
- **PostgreSQL Database** (Agent registration & metadata)
- **Redis** (WebSocket connections & offline message queue)

## Zeabur Configuration

### zeabur.yaml

```yaml
# Zeabur deployment configuration
name: AgentLink
region: us-east-1  # or your preferred region

services:
  - type: backend
    name: relay-server
    source: ./server
    dockerfilePath: Dockerfile
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    env:
      - key: PORT
        value: "8000"
      - key: DATABASE_URL
        fromSecret: DATABASE_URL
      - key: REDIS_URL
        fromSecret: REDIS_URL
      - key: ETH_CHAIN_ID
        value: "84532"  # Base Sepolia testnet
      - key: ETH_RPC_URL
        fromSecret: ETH_RPC_URL
      - key: ANTHROPIC_API_KEY
        fromSecret: ANTHROPIC_API_KEY
    plan: hobby  # upgrade to 'production' as needed

databases:
  - type: postgres
    name: agentlink-db
    plan: hobby  # 1GB storage, 100MB RAM

caches:
  - type: redis
    name: agentlink-cache
    plan: hobby  # 100MB storage

domains:
  - name: agentlink.zeabur.app  # replace with your custom domain
    service: relay-server
```

## Environment Variables

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `REDIS_URL` | Redis connection string | `redis://host:6379` |
| `ETH_CHAIN_ID` | Ethereum chain ID | `84532` (Base Sepolia) |
| `ETH_RPC_URL` | Ethereum RPC endpoint | `https://base-sepolia.infura.io/v3/...` |
| `ANTHROPIC_API_KEY` | Claude API key (optional) | `sk-ant-...` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Server port | `8000` |
| `DEBUG` | Enable debug mode | `false` |
| `CORS_ORIGINS` | CORS allowed origins | `*` |
| `MESSAGE_TTL` | Offline message TTL (seconds) | `604800` (7 days) |

## Deployment Steps

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Initial AgentLink project structure"
git push origin main
```

### 2. Create Project on Zeabur

1. Go to https://zeabur.com
2. Click "Create Project"
3. Select "Import from GitHub"
4. Choose `kimireg/AgentLink` repository
5. Zeabur will auto-detect the project type

### 3. Configure Services

**PostgreSQL Database:**
- Name: `agentlink-db`
- Plan: `hobby` (free tier sufficient for MVP)
- Zeabur will auto-inject `DATABASE_URL` as secret

**Redis Cache:**
- Name: `agentlink-cache`
- Plan: `hobby` (free tier)
- Zeabur will auto-inject `REDIS_URL` as secret

**Backend Service:**
- Name: `relay-server`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Environment variables: Add secrets via Zeabur dashboard

### 4. Deploy

- Zeabur will automatically build and deploy on `git push`
- Monitor deployment logs in Zeabur dashboard
- Access API at: `https://relay-server.your-project.zeabur.app`

### 5. Verify Deployment

```bash
# Test Agent registration
curl -X POST https://relay-server.your-project.zeabur.app/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "owner_address": "0x7a3b...",
    "agent_name": "Test Agent",
    "capabilities": ["chat"],
    "encryption_pubkey": "..."
  }'

# Test AgentCard query
curl https://relay-server.your-project.zeabur.app/agent/1
```

## Monitoring & Logs

### Access Logs

- Zeabur Dashboard → Project → Logs
- Real-time WebSocket connection logs
- HTTP request/response logs

### Metrics

- CPU/Memory usage
- Database connections
- Redis memory usage
- Request rate & latency

### Health Check

Zeabur automatically monitors:
- HTTP health endpoint (`/health`)
- Database connectivity
- Redis connectivity

Add custom health check in `server/main.py`:

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "connected",
        "redis": "connected"
    }
```

## Scaling Considerations

### Current Limits (Hobby Plan)

| Resource | Limit |
|----------|-------|
| CPU | 0.5 vCPU |
| Memory | 512 MB |
| Database Storage | 1 GB |
| Redis Storage | 100 MB |
| Bandwidth | 100 GB/month |

### When to Upgrade

Upgrade to `production` plan when:
- > 100 concurrent WebSocket connections
- > 10,000 messages/day
- Database storage > 1 GB
- Redis memory > 100 MB

### Scaling Strategy

1. **Vertical Scaling**: Increase CPU/Memory (Zeabur handles automatically)
2. **Horizontal Scaling**: Multiple relay instances (requires Redis pub/sub)
3. **Database Scaling**: Upgrade PostgreSQL plan or use read replicas
4. **Redis Scaling**: Upgrade Redis plan or use cluster mode

## Cost Estimation

| Component | Hobby Plan | Production Plan |
|-----------|------------|-----------------|
| Compute | $0/month | $15/month |
| PostgreSQL | $0/month | $15/month |
| Redis | $0/month | $10/month |
| **Total** | **$0/month** | **$40/month** |

**Recommendation**: Start with Hobby plan, monitor usage, upgrade as needed.

## Troubleshooting

### Deployment Fails

**Check:**
1. `requirements.txt` has all dependencies
2. `server/main.py` exists and is valid Python
3. Environment variables are set in Zeabur dashboard
4. Database migrations ran successfully

**Fix:**
```bash
# Run migrations manually via Zeabur shell
zeabur shell
python -m alembic upgrade head
```

### WebSocket Connection Fails

**Check:**
1. SSL/TLS is enabled (Zeabur provides automatically)
2. WebSocket endpoint is `/ws` (not `/websocket`)
3. CORS is configured correctly
4. Firewall allows WebSocket traffic (Zeabur handles)

**Fix:**
```python
# In server/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Database Connection Fails

**Check:**
1. `DATABASE_URL` secret is set correctly
2. Database is running (check Zeabur dashboard)
3. Network connectivity between compute and database

**Fix:**
```bash
# Test connection locally
export DATABASE_URL="postgresql://..."
python -c "from sqlalchemy import create_engine; engine = create_engine(os.getenv('DATABASE_URL')); print('Connected!')"
```

## Backup & Recovery

### Database Backups

Zeabur automatically backs up PostgreSQL:
- Daily snapshots
- Retained for 7 days
- Manual restore via dashboard

### Redis Persistence

Redis data is ephemeral (in-memory):
- Offline messages expire after TTL (default 7 days)
- Connection state is lost on restart (agents reconnect)

### Manual Backup

```bash
# Export database
pg_dump $DATABASE_URL > backup.sql

# Import database
psql $DATABASE_URL < backup.sql
```

## Security Best Practices

1. **Never commit secrets** to Git (use `.env` + `.gitignore`)
2. **Use HTTPS only** (Zeabur enforces automatically)
3. **Enable CORS restrictions** in production (not `*`)
4. **Rotate secrets** periodically (database password, API keys)
5. **Monitor logs** for suspicious activity
6. **Rate limit** API endpoints (consider adding in Phase 2)

## Next Steps

1. ✅ Push code to GitHub
2. ✅ Create Zeabur project
3. ✅ Configure services and secrets
4. ✅ Deploy and verify
5. ✅ Test with Local Agent SDK

---

**Last Updated**: 2026-02-13
**Version**: 1.0
