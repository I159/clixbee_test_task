# Ad Exchange Auction Service

Simplified ad exchange auction service implementing real-time bidding, rate limiting, and statistics tracking.

## How to Start (Docker Compose)

### Prerequisites
- Docker and Docker Compose installed

### Starting the Service

1. Clone the repository and navigate to the project directory:
```bash
cd ad-exchange-auction
```

2. Start the services:
```bash
docker-compose up --build
```

This will start:
- **Redis** on port 6379 (for rate limiting and statistics)
- **App** on port 8000 (FastAPI with 3 Uvicorn workers)

3. Test the service:
```bash
# Run an auction
curl -X POST http://localhost:8000/bid \
  -H "Content-Type: application/json" \
  -H "X-Country: US" \
  -d '{"supply_id": "supply1"}'

# Get statistics
curl http://localhost:8000/stat
```

### Configuration
Environment variables can be set in `docker-compose.yaml`:
- `REDIS_HOST` - Redis hostname (default: redis)
- `REDIS_PORT` - Redis port (default: 6379)

Additional settings in `ad_exchange_auction/settings.py`:
- `rate_limit_window_seconds` - Rate limit window (default: 60)
- `rate_limit_max_requests` - Max requests per window (default: 3)

## Architecture Overview

### Request Flow
```
Client → Rate Limiter → Auction → Statistics Recording
                           ↓
                    Bidder Selection → Winner Determination
```

### Core Components

**1. FastAPI Application (`app.py`)**
- Entry point handling `/bid` (POST) and `/stat` (GET) endpoints
- Manages global state (repositories, pending tasks)
- Coordinates rate limiting, auction execution, and statistics

**2. Auction Engine (`core/auction.py`)**
- Filters eligible bidders by country and supply
- Executes synchronous bidding process
- Determines winner (highest bid)
- Spawns async task for statistics recording

**3. Rate Limiter (`core/rate_limiter.py`)**
- Sliding window algorithm using Redis sorted sets
- Prevents burst traffic across window boundaries
- Tracks requests per IP with timestamp precision

**4. Statistics System (`core/statistics.py`)**

Statistics recording is asynchronous to avoid blocking the auction response:

**Architecture:**
- Each auction spawns a background task via `asyncio.create_task()`
- Tasks are stored in global `app.state.pending_stats_tasks` set
- Redis keys structured as `stats:{supply_id}:{metric}` for atomic increments
- `/stat` endpoint waits for pending tasks via `asyncio.gather()` before reading
- Tasks self-remove from set via `add_done_callback()` on completion

**Design rationale:**
- Auction completes immediately without waiting for Redis I/O
- `/stat` ensures all in-flight updates complete before aggregating results
- Shared pending tasks set prevents race conditions between writes and reads
- Statistics are eventually consistent with minimal lag

**Trade-off:**
- `/stat` endpoint may wait briefly if many auctions are in-flight
- Alternative would be message queue for higher scale

**5. Data Repositories (`core/repository.py`)**
- In-memory storage loaded from JSON at startup
- `SupplyRepository`: Maps supply IDs to eligible bidder IDs
- `BidderRepository`: Stores bidder metadata (ID, country)

## Scaling

### Already Implemented

**1. Multi-worker Deployment**
- 3 Uvicorn workers configured in Dockerfile
- Horizontal scaling ready (stateless application)
- Redis provides shared state across workers

**2. Async Statistics Recording**
- Non-blocking writes to Redis
- Prevents auction path blocking on I/O
- Background tasks run independently

**3. Rate Limiting Infrastructure**
- Per-IP tracking scales independently
- Redis sorted sets provide efficient operations
- Automatic expiration prevents memory bloat

**4. In-Memory Repository Cache**
- Bidder/supply data loaded once at startup
- Eliminates database queries during auction hot path
- Suitable for relatively static datasets

### Further Improvements

**1. Database Backend**
- Replace JSON files with PostgreSQL/MongoDB
- Periodic cache refresh from database
- Supports dynamic bidder/supply updates

**2. Redis Clustering**
- Partition statistics by supply ID (natural sharding key)
- Separate Redis instances for rate limiting vs statistics
- Reduce single-point bottleneck

**3. Message Queue for Statistics**
- Replace `asyncio.create_task()` with an MQ
- Dedicated statistics worker processes
- Better backpressure handling under extreme load

**4. Caching Layer**
- Redis/Memcached for `/stat` endpoint results
- TTL-based invalidation
- Reduces Redis key scanning overhead

**5. Async Bidder Communication**
- Current design simulates bids synchronously
- Real-world: Parallel HTTP requests to bidder endpoints
- `asyncio.gather()` for concurrent bid collection
- Timeout handling for slow bidders

**6. Load Balancer**
- Connection pooling optimization
- Reduced Redis connection overhead per worker

**7. Optimized Statistics Queries**
- Replace `redis_client.keys()` with Redis Sets tracking active supply/bidder IDs
- Current implementation uses O(N) scan (non-production pattern)
- Use Redis Hash structures for grouped statistics
