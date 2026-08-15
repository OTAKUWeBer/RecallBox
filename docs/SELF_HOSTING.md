# Self-Hosting RecallBox

RecallBox is designed for straightforward self-hosting on your local workstation, home server, NAS, or private VPS.

---

## 1. Quickstart with Docker Compose

```bash
# 1. Clone repository
git clone https://github.com/OTAKUWeBer/RecallBox.git
cd recallbox

# 2. Launch the stack
docker compose up -d
```

- **Web UI**: Access at [http://localhost:3000](http://localhost:3000)
- **Backend API**: Access at [http://127.0.0.1:8765/api/v1](http://127.0.0.1:8765/api/v1)
- **Health Check**: [http://127.0.0.1:8765/api/v1/health](http://127.0.0.1:8765/api/v1/health)

---

## 2. Security & Network Configuration

By default, `docker-compose.yml` binds ports exclusively to `127.0.0.1` (`127.0.0.1:8765:8765` and `127.0.0.1:3000:3000`). This ensures that your private memories are not accidentally accessible to other devices on your Local Area Network (LAN) or public Wi-Fi.

### Exposing to a Private Home Server / LAN
If you are hosting RecallBox on a dedicated home server (e.g. Raspberry Pi, Unraid, TrueNAS) and wish to access it from other devices on your home network:

1. Update the port mappings in `docker-compose.yml`:
   ```yaml
   ports:
     - "0.0.0.0:8765:8765"
   ```
2. Set a strong secret authorization token in your `.env` file:
   ```env
   RECALLBOX_API_KEY=your_strong_random_secret_token_here
   ```
3. Restart the container:
   ```bash
   docker compose up -d --force-recreate
   ```

---

## 3. Data Persistence & Backups

All user data is stored inside the `recallbox_data` Docker volume:
- `data/recallbox.db`: Main SQLite database (WAL mode).
- `data/auth_token`: Cryptographic local loopback token.
- `data/attachments/`: Local attachments and screenshots.

### Creating a Backup
```bash
# 1. Download complete ZIP export via Web UI or API:
curl -H "X-RecallBox-Key: <token>" http://127.0.0.1:8765/api/v1/export/zip -o backup-recallbox-$(date +%Y%m%d).zip

# 2. Or copy the SQLite database file directly:
cp data/recallbox.db backup-recallbox-$(date +%Y%m%d).db
```
