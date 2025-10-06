# Docker Desktop Reset - Exact Steps

## **Method 1: Via Docker Desktop Menu (Easiest)**

1. **Click the Docker icon** in your Mac menu bar (top right, looks like a whale)
2. Click **"Troubleshoot"** in the dropdown menu
3. Click **"Reset to factory defaults..."**
4. Confirm the reset
5. Wait for Docker to restart

## **Method 2: Via Settings (Alternative)**

1. Open **Docker Desktop** application
2. Click the **gear icon ⚙️** (top right) to open Settings
3. In the left sidebar, scroll down and find **"Troubleshoot"**
4. On the right panel, look for **"Clean / Purge data"** section
5. Click **"Reset to factory defaults"**
6. Confirm

## **Method 3: Command Line (Fastest)**

If you can't find the UI option, just run this:

```bash
# Stop Docker Desktop
osascript -e 'quit app "Docker"'

# Wait for it to quit
sleep 10

# Remove all Docker data
rm -rf ~/Library/Containers/com.docker.docker/Data/vms/0/data

# Or for complete reset:
# rm -rf ~/Library/Containers/com.docker.docker/Data

# Restart Docker
open -a Docker

# Wait for initialization
echo "Waiting for Docker to start..."
sleep 30

# Test
docker info
```

## **Method 4: Nuclear Option**

If nothing else works:

```bash
# 1. Quit Docker
osascript -e 'quit app "Docker"'
sleep 5

# 2. Delete everything
rm -rf ~/Library/Containers/com.docker.docker
rm -rf ~/Library/Group\ Containers/group.com.docker

# 3. Reinstall Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Or via Homebrew:
# brew install --cask docker
```

## **Quick Command to Run:**

Just copy and paste this:

```bash
osascript -e 'quit app "Docker"' && \
sleep 5 && \
rm -rf ~/Library/Containers/com.docker.docker/Data && \
open -a Docker && \
echo "Docker is resetting... wait 30 seconds" && \
sleep 30 && \
docker info
```

This will:
- Quit Docker
- Remove corrupted data
- Restart Docker fresh
- Test that it's working
