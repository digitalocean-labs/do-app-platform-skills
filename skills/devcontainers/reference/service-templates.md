# Service Templates

Complete docker-compose service configurations for all supported backing services.

## Base Structure

```yaml
services:
  app:
    image: mcr.microsoft.com/devcontainers/base:noble
    profiles: [ "app" ]
    volumes:
      - ..:/workspaces/app:cached
      - ${GIT_COMMON_DIR}:${GIT_COMMON_DIR}:cached
      - app-config:/home/vscode/.config
      - claude-config:/home/vscode/.claude
    command: sleep infinity
    networks:
      - devcontainer-network

  # Add service blocks below based on requirements

volumes:
  app-config:
  claude-config:
  # Add service-specific volumes

networks:
  devcontainer-network:
    driver: bridge
```

---

## PostgreSQL

```yaml
postgres:
  image: postgres:18
  profiles: [ "postgres" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:5432"
  environment:
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: password
    POSTGRES_DB: app
  volumes:
    - postgres-data:/var/lib/postgresql
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Connection string:** `postgresql://postgres:password@postgres:5432/app`

---

## MySQL

```yaml
mysql:
  image: mysql:8
  profiles: [ "mysql" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:3306"
  environment:
    MYSQL_ROOT_PASSWORD: password
    MYSQL_DATABASE: app
    MYSQL_USER: mysql
    MYSQL_PASSWORD: mysql
  volumes:
    - mysql-data:/var/lib/mysql
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-ppassword"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Connection string:** `mysql://mysql:mysql@mysql:3306/app`

---

## MongoDB

```yaml
mongo:
  image: mongo:8
  profiles: [ "mongo" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:27017"
  environment:
    MONGO_INITDB_ROOT_USERNAME: mongodb
    MONGO_INITDB_ROOT_PASSWORD: mongodb
    MONGO_INITDB_DATABASE: app
  volumes:
    - mongo-data:/data/db
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Connection string:** `mongodb://mongodb:mongodb@mongo:27017/app?authSource=admin`

---

## Valkey (Redis-compatible)

```yaml
valkey:
  image: valkey/valkey:8
  profiles: [ "valkey" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:6379"
  volumes:
    - valkey-data:/data
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD", "valkey-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Connection string:** `redis://valkey:6379`

---

## Kafka (KRaft mode - no Zookeeper)

```yaml
kafka:
  image: confluentinc/cp-kafka:7.7.0
  profiles: [ "kafka" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:9092"
  environment:
    KAFKA_NODE_ID: 1
    CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
    KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
    KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
    KAFKA_NUM_PARTITIONS: 1
  volumes:
    - kafka-data:/var/lib/kafka/data
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD-SHELL", "kafka-broker-api-versions --bootstrap-server localhost:9092 || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 60s
```

**Bootstrap servers:** `kafka:9092`

**Note:** Kafka in KRaft mode takes 60+ seconds to initialize. The healthcheck has `start_period: 60s`.

---

## RustFS (S3-compatible Storage)

```yaml
# Profile name "minio" kept for backward compatibility
minio:
  image: rustfs/rustfs:latest
  profiles: [ "minio" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:9000"  # API (S3-compatible)
    - "127.0.0.1:0:9001"  # Console
  volumes:
    - minio-data:/data
    - minio-logs:/logs
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD", "curl", "-sf", "http://localhost:9000/health"]
    interval: 30s
    timeout: 20s
    retries: 3
```

**Credentials:** `rustfsadmin` / `rustfsadmin`
**Endpoint:** `http://minio:9000`

---

## OpenSearch

```yaml
opensearch:
  image: opensearchproject/opensearch:3.0.0
  profiles: [ "opensearch" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:9200"
    - "127.0.0.1:0:9300"
  environment:
    - discovery.type=single-node
    - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    - "DISABLE_INSTALL_DEMO_CONFIG=true"
    - "DISABLE_SECURITY_PLUGIN=true"
  volumes:
    - opensearch-data:/usr/share/opensearch/data
  networks:
    - devcontainer-network
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:9200/_cluster/health || exit 1"]
    interval: 30s
    timeout: 10s
    retries: 5
    start_period: 60s

opensearch-dashboards:
  image: opensearchproject/opensearch-dashboards:3.0.0
  profiles: [ "opensearch" ]
  restart: unless-stopped
  ports:
    - "127.0.0.1:0:5601"
  environment:
    - "OPENSEARCH_HOSTS=http://opensearch:9200"
    - "DISABLE_SECURITY_DASHBOARDS_PLUGIN=true"
  depends_on:
    opensearch:
      condition: service_healthy
  networks:
    - devcontainer-network
```

**Endpoint:** `http://opensearch:9200`

**Note:** OpenSearch needs 30-60s to start. Increase JVM heap if out of memory:
```yaml
environment:
  - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
```

---

## Connection String Summary

| Service | Connection String |
|---------|-------------------|
| PostgreSQL | `postgresql://postgres:password@postgres:5432/app` |
| MySQL | `mysql://mysql:mysql@mysql:3306/app` |
| MongoDB | `mongodb://mongodb:mongodb@mongo:27017/app?authSource=admin` |
| Valkey | `redis://valkey:6379` |
| Kafka | `kafka:9092` |
| RustFS | `http://minio:9000` |
| OpenSearch | `http://opensearch:9200` |

---

## App Platform to Local Mapping

| App Platform | Local Container | Profile |
|--------------|-----------------|---------|
| `databases[].engine: PG` | `postgres:18` | `postgres` |
| `databases[].engine: MYSQL` | `mysql:8` | `mysql` |
| `databases[].engine: MONGODB` | `mongo:8` | `mongo` |
| `databases[].engine: REDIS` | `valkey/valkey:8` | `valkey` |
| Spaces attachment | `rustfs/rustfs:latest` | `minio` |
| (future) Kafka managed | `confluentinc/cp-kafka:7.7.0` | `kafka` |

---

## Volume Declarations

Add these to your `volumes:` section based on services used:

```yaml
volumes:
  app-config:
  claude-config:
  postgres-data:
  mysql-data:
  mongo-data:
  valkey-data:
  kafka-data:
  minio-data:
  minio-logs:
  opensearch-data:
```

---

## Health Check Timing

| Service | Ready Time | Notes |
|---------|------------|-------|
| PostgreSQL | <10s | Fast startup |
| MySQL | <10s | Fast startup |
| MongoDB | <10s | Fast startup |
| Valkey | <10s | Fast startup |
| RustFS | <10s | Fast startup |
| Kafka | 60s+ | KRaft initialization |
| OpenSearch | 30-60s | JVM warmup |
