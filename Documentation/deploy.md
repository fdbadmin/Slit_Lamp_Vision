# Deploy (macOS → Pi over SSH)

## Prereqs

- Pi is reachable over the network (e.g., `slitlamp.local`)
- SSH works: `ssh pi@slitlamp.local`

## One-time: deploy + bootstrap

On macOS:

```bash
PI_HOST=slitlamp.local ./scripts/deploy_rsync.sh
```

On the Pi:

```bash
cd ~/slit-lamp-camera
./scripts/pi_bootstrap.sh
```

## Update loop

On macOS:

```bash
PI_HOST=slitlamp.local ./scripts/deploy_rsync.sh
```

On the Pi:

```bash
cd ~/slit-lamp-camera
./scripts/pi_update.sh
```
