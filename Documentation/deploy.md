# Deployment Guide

Deploy the Slit Lamp Camera software from your development machine to a Raspberry Pi.

## Prerequisites

- Pi is reachable over the network (e.g., `vision.local`)
- SSH works: `ssh admin@vision.local`
- Git repository cloned locally

## First-Time Setup (New Pi)

Deploy code and run full setup in one command:

```bash
PI_HOST=vision.local ./scripts/deploy_rsync.sh --setup
```

This will:
1. Sync all code to the Pi
2. Install system packages
3. Create Python venv
4. Install systemd services
5. Configure USB automount
6. Run verification checks

## Update Existing Installation

After making code changes, deploy updates:

```bash
PI_HOST=vision.local ./scripts/deploy_rsync.sh
```

Then restart the service on the Pi:

```bash
ssh admin@vision.local 'sudo systemctl restart slitcam-recorder.service'
```

Or use the update script:

```bash
ssh admin@vision.local 'cd ~/slit-lamp-camera && ./scripts/pi_update.sh'
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PI_HOST` | (required) | Pi hostname or IP |
| `PI_USER` | `admin` | SSH username |
| `PI_DIR` | `/home/$PI_USER/slit-lamp-camera` | Target directory |

## Examples

```bash
# Deploy to Pi named "vision"
PI_HOST=vision.local ./scripts/deploy_rsync.sh

# Deploy to Pi by IP address
PI_HOST=192.168.1.100 ./scripts/deploy_rsync.sh

# Deploy with custom username
PI_USER=pi PI_HOST=slitlamp.local ./scripts/deploy_rsync.sh

# Full setup (first time)
PI_HOST=vision.local ./scripts/deploy_rsync.sh --setup
```

## What Gets Synced

The rsync command syncs the entire project except:
- `.git/` - Git repository data
- `.venv/` - Python virtual environment (created on Pi)
- `__pycache__/` - Python cache
- `.pytest_cache/` - Test cache
- `.ruff_cache/` - Linter cache
- `setup.log` - Setup log file

## Troubleshooting

### SSH connection refused

```bash
# Check Pi is online
ping vision.local

# Check SSH service on Pi
ssh admin@vision.local 'sudo systemctl status ssh'
```

### Permission denied

```bash
# Ensure SSH key is added
ssh-copy-id admin@vision.local
```

### Hostname not found

```bash
# Use IP address instead
PI_HOST=192.168.1.100 ./scripts/deploy_rsync.sh

# Or check mDNS
ping vision.local
```
