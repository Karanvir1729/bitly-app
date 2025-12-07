# Bitly-Style URL Shortener (Redis and Cassandra)

A minimal URL shortener API implemented twice to compare datastore choices:

- Redis: in-memory key/value store with a simple Flask API and a Dockerized deployment.
- Cassandra: distributed wide-column store with a Flask API and helper scripts to start/stop a small Cassandra cluster on remote hosts.

Both services expose the same HTTP interface:

- POST `/shorten` — create a short code for a long URL
- GET `/<code>` — redirect to the original URL


## Repository Layout

- `Redis/`
  - `main.py` — Flask app backed by Redis
  - `requirements.txt` — Python dependencies for the Redis app
  - `Dockerfile` — container image for the API (served by gunicorn)
  - `docker-compose.yml` — Docker Swarm stack file with Redis + API services
- `Cassandra/`
  - `main.py` — Flask app backed by Cassandra
  - `startCluster.sh` — helper to start Cassandra nodes on remote hosts via SSH + Docker
  - `stopCluster.sh` — helper to stop/remove those nodes


## API

Base URL is configurable via `BASE_URL` (used to build returned short links). By default:

- Redis app defaults to `http://localhost/`
- Cassandra app defaults to `http://localhost:8000/`

Endpoints:

- POST `/shorten`
  - Request (JSON): `{ "url": "https://example.com/long", "code": "mycode" }`
  - Validations: both fields required; `code` must be alphanumeric; conflict (409) if `code` already exists
  - Response (201): `{ "code": "mycode", "short_url": "<BASE_URL>/mycode", "original_url": "..." }`
- GET `/<code>`
  - Redirects (302) to the original URL
  - 404 if the code is unknown

Example (curl):

```bash
curl -X POST http://localhost:8000/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url": "https://example.com/long-path", "code": "ex1"}'

curl -i http://localhost:8000/ex1
```


## Running the Redis Version

You can run it locally with Python, or via Docker. The provided `docker-compose.yml` targets Docker Swarm (deploy section + overlay network).

### Option A: Local (Python)

Requirements:
- Python 3.11+
- Redis server reachable at `REDIS_HOST:REDIS_PORT` (defaults to `localhost:6379`)

Setup:

```bash
cd Redis
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export BASE_URL=http://localhost:8000
python main.py  # serves on http://0.0.0.0:8000
```

### Option B: Docker (single container)

Build and run the API image; connect it to a running Redis container or external Redis:

```bash
cd Redis
# Start a Redis container (for local dev)
docker run -d --name redis -p 6379:6379 redis:7

# Build API image
docker build -t bitly-api:v2 .

# Run API container
docker run --rm -p 8000:8000 \
  -e REDIS_HOST=host.docker.internal \
  -e REDIS_PORT=6379 \
  -e REDIS_DB=0 \
  -e BASE_URL=http://localhost:8000 \
  bitly-api:v2
```

### Option C: Docker Swarm (stack deploy)

The `docker-compose.yml` is written for Swarm (uses deploy settings and an overlay network). To deploy:

```bash
cd Redis
# Initialize Swarm (on a single node or a cluster)
docker swarm init  # skip if already initialized

# Deploy the stack (name: bitly)
docker stack deploy -c docker-compose.yml bitly

# Inspect services
docker stack services bitly
```

Environment passed to the API service in the compose file:

- `REDIS_HOST=redis`
- `REDIS_PORT=6379`
- `REDIS_DB=0`
- `BASE_URL=http://10.128.0.3` (adjust to your external address)


## Running the Cassandra Version

Requirements:
- Python 3.11+
- `cassandra-driver` package
- Access to a Cassandra cluster (or containers) reachable from the app

Install dependencies and run:

```bash
cd Cassandra
python -m venv .venv && source .venv/bin/activate
pip install Flask cassandra-driver

# Point to your cluster contact points and desired keyspace
export CASSANDRA_CONTACT_POINTS=10.128.0.3,10.128.0.4,10.128.0.5
export CASSANDRA_KEYSPACE=urlshortener
export CASSANDRA_RF=3
export BASE_URL=http://localhost:8000

python main.py  # serves on http://0.0.0.0:8000
```

On startup the app:
- Creates the keyspace (if missing) with the provided replication factor
- Ensures the `urls(code text PRIMARY KEY, original_url text)` table exists

### Optional: Start/Stop a small Cassandra cluster via SSH + Docker

The helper scripts expect passwordless SSH to remote hosts as user `thekaranvir`, and Docker available on those hosts.

- `startCluster.sh IP1 IP2 IP3 ...` — starts a containerized Cassandra node on each host, seeding to the first IP; waits until each node is `UN` (Up/Normal) via `nodetool status`
- `stopCluster.sh IP1 IP2 IP3 ...` — stops/removes the `cassandra-node` container on each host

Notes:
- Adjust the SSH user or script as needed for your environment
- The scripts map `7000` and `9042` on each host; ensure ports are available


## Configuration Reference

Common:
- `BASE_URL` — base used to construct returned short links, e.g. `http://localhost:8000`

Redis app:
- `REDIS_HOST` (default: `localhost`)
- `REDIS_PORT` (default: `6379`)
- `REDIS_DB` (default: `0`)

Cassandra app:
- `CASSANDRA_CONTACT_POINTS` (comma-separated, default: `10.128.0.3,10.128.0.4,10.128.0.5`)
- `CASSANDRA_KEYSPACE` (default: `urlshortener`)
- `CASSANDRA_RF` (replication factor, default: `3`)


## Development Notes and Limitations

- No authentication or rate limiting — suitable for demos/tests only.
- Codes are client-provided and must be alphanumeric. There is no automatic code generation.
- No TTLs or analytics; feel free to extend for your use-case (e.g., click counts, expiration, QR codes).
- The Redis `docker-compose.yml` uses Swarm constructs; for plain `docker compose`, remove the `deploy` and `placement` sections and switch to a bridge network.


## License

No license file is provided. If you plan to publish or share, add an appropriate LICENSE.

