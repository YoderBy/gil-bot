## Purpose

Step‑by‑step, fool‑proof guide to the homelab reverse‑proxy + CI/CD stack we just finished.  Any professional (or future‑me) should be able to reproduce, operate and debug the system armed only with this file.

## Topology at a glance

* Host: Ubuntu 24.04 server on HP Envy laptop, LAN IP **10.0.0.13**.
* Public domain **yosefbyd.com** managed in Cloudflare.
* Cloudflare Tunnel ID **ea82966b‑…** terminates TLS and forwards traffic to the host.
* One wildcard CNAME `*.yosefbyd.com → ea82966b-…cfargotunnel.com` (Proxied).
* **Traefik v3** is the single reverse‑proxy on the host (port 80) and serves an internal dashboard on port 8080.
* All application containers live on the custom Docker network **proxy** and expose themselves through Traefik by means of labels – no host port bindings.
* Continuous delivery handled by **Watchtower** (pulls latest images) and **GitHub Actions** (build + push to the private registry).

## 0 — Prerequisites on a fresh host

1. Ubuntu server with Docker CE, docker-compose v2, and UFW rule `sudo ufw allow 80/tcp`.
2. A Cloudflare account with the zone **yosefbyd.com** and a created Tunnel (Cloudflared authenticated once).
3. The host can resolve external DNS.
4. SSH open locally (`ssh yoder@10.0.0.13`) and via Cloudflare (`ssh homelab`).
5. **On the Docker host (`10.0.0.13`), authenticate with your private registry:**
   ```bash
   docker login registry.yosefbyd.com
   # (Enter yoder and your <STRONG_PASSWORD> when prompted)
   ```
   This allows the host to pull images for new services. This is a one-time setup on the host.

---

## 1 — Cloudflare configuration (one‑time)

### 1.1 DNS

```
Type  Name     Value (target)                       Proxy
CNAME *.yosefbyd.com  ea82966b-….cfargotunnel.com   Proxied
CNAME ssh            ea82966b-….cfargotunnel.com   Proxied (optional)
```

*The wildcard eliminates future manual DNS edits.*

### 1.2 Access (optional hardening)

In **Zero‑Trust → Access → Applications** add policies so sensitive routes (Portainer, Netdata, Traefik) require e‑mail/SSO.

---

## 2 — Cloudflared service on the host

`/etc/cloudflared/config.yml`

```yaml
tunnel: ea82966b-aec9-4ca4-911e-b0b6deffec3b
credentials-file: /home/yoder/.cloudflared/ea82966b-aec9-4ca4-911e-b0b6deffec3b.json

ingress:
  - hostname: '*.yosefbyd.com'
    service: http://localhost:80   # Traefik
  - hostname: 'ssh.yosefbyd.com'
    service: ssh://localhost:22
  - service: http_status:404       # catch‑all
```

Reload: `sudo systemctl restart cloudflared`.

Trouble‑shoot: `journalctl -u cloudflared -f`.

---

## 3 — Docker network & Traefik core

```bash
docker network create proxy

# Note: The registry container (Section 5.3) should be started with REGISTRY_HTTP_RELATIVEURLS=true
# -e REGISTRY_HTTP_RELATIVEURLS=true
# This ensures Docker clients correctly handle redirects when pushing/pulling.

docker run -d --name traefik --restart=always \
  -p 80:80 -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --network proxy \
  traefik:v3 \
    --entrypoints.web.address=:80 \
    --api.insecure=true \
    --api.dashboard=true \
    --providers.docker \
    --providers.docker.network=proxy \
    --providers.docker.exposedbydefault=false \
    --providers.docker.defaultRule='Host(`{{ .Name }}.yosefbyd.com`)'
```

* **Port 80** – wildcard HTTP from Cloudflare.
* **Port 8080** – dashboard (LAN only).
* `defaultRule` = `<container‑name>.yosefbyd.com`.
* `exposedbydefault=false` means a container is *not* public unless it sets `traefik.enable=true`.

Verify:

```
curl http://10.0.0.13:80/      # should answer 404 but from Traefik
open http://10.0.0.13:8080/dashboard/  # UI should load
```

---

## 4 — Template for an application container

This section describes how to define and initially deploy a *new* application (e.g., `myapi`) into the CI/CD stack.

**A. Define your application (e.g., in its own `docker-compose.yml` or as a `docker run` command):**

```yaml
# Example using docker-compose.yml for a new service 'myapi'
services:
  myapi:
    image: registry.yosefbyd.com/myapi:latest  # This image will be built by GitHub Actions
    restart: always
    networks:
      - proxy  # Connects to Traefik's network
    labels:
      - traefik.enable=true
      # Specifies the internal port the 'myapi' container listens on
      - traefik.http.services.myapi.loadbalancer.server.port=8080 # Adjust if your app uses a different port
      # Defines the public URL, e.g., https://myapi.yosefbyd.com
      # Traefik's defaultRule (Section 3) might cover this if your service name matches 'myapi'
      # - "traefik.http.routers.myapi.rule=Host(`myapi.yosefbyd.com`)"
```

*No `ports:` section (host port bindings) is required for the application container itself; Traefik handles external access.*

**B. Perform the *initial* deployment on your Docker host (`10.0.0.13`):**

To make Watchtower aware of your new application and for Traefik to route to it, you must start it manually once.
Ensure you have run `docker login registry.yosefbyd.com` on the host first (see Section 0).

*   **If using `docker-compose.yml` for your application:**
    ```bash
    # On your Docker host, navigate to the directory containing your app's docker-compose.yml
    # cd /path/to/your/myapi/project
    docker-compose up -d myapi
    ```
*   **If using a `docker run` command:**
    ```bash
    docker run -d --name myapi --restart=always \
      --network proxy \
      -l traefik.enable=true \
      -l traefik.http.services.myapi.loadbalancer.server.port=8080 \
      # Optional: Explicitly set the rule if not relying on Traefik's defaultRule
      # -l "traefik.http.routers.myapi.rule=Host(`myapi.yosefbyd.com`)" \
      registry.yosefbyd.com/myapi:latest
    ```

*After this initial start, the application (e.g., `myapi`) will be running and accessible (e.g., at `https://myapi.yosefbyd.com`) within ~5-15 seconds. Watchtower will then monitor this running container for image updates pushed by GitHub Actions.*

---

## 5 — Core service containers

### 5.1 Portainer CE

```bash
docker run -d --name portainer --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v portainer_data:/data \
  --network proxy \
  -l traefik.enable=true \
  -l traefik.http.services.portainer.loadbalancer.server.port=9000 \
  portainer/portainer-ce:latest
```

*URL*: `https://portainer.yosefbyd.com`

### 5.2 Netdata

```bash
docker run -d --name netdata --restart=always \
  --cap-add SYS_PTRACE --cap-add SYS_RAWIO --privileged \
  -v netdata_lib:/var/lib/netdata \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /etc/os-release:/host/etc/os-release:ro \
  --network proxy \
  -l traefik.enable=true \
  -l traefik.http.services.netdata.loadbalancer.server.port=19999 \
  netdata/netdata
```

*URL*: `https://netdata.yosefbyd.com`

### 5.3 Private Docker Registry

```bash
# create once
sudo mkdir -p /opt/registry/auth

docker run --rm httpd:2.4-alpine htpasswd -nbB yoder <STRONG_PASSWORD> \
  | sudo tee /opt/registry/auth/htpasswd

docker run -d --name registry --restart=always \
  -v registry_data:/var/lib/registry \
  -v /opt/registry/auth:/auth \
  -e REGISTRY_HTTP_ADDR=0.0.0.0:5000 \
  -e REGISTRY_HTTP_RELATIVEURLS=true \
  # The REGISTRY_HTTP_RELATIVEURLS=true line above is crucial for correct client redirects, 
  # preventing 401 errors during pushes from GitHub Actions or local Docker clients.
  -e REGISTRY_AUTH=htpasswd \
  -e REGISTRY_AUTH_HTPASSWD_REALM='Registry' \
  -e REGISTRY_AUTH_HTPASSWD_PATH=/auth/htpasswd \
  --network proxy \
  -l traefik.enable=true \
  -l traefik.http.services.registry.loadbalancer.server.port=5000 \
  registry:2
```

*URL*: `https://registry.yosefbyd.com`
Testing:

```
docker login registry.yosefbyd.com
curl -I -H "Host: registry.yosefbyd.com" http://10.0.0.13/v2/   # 401 = healthy
```

---

## 6 — Watchtower (auto‑update running containers)

To enable Watchtower to pull images from your private registry (`registry.yosefbyd.com`), it needs access to the Docker credentials that were set up when you ran `docker login registry.yosefbyd.com` on the host (as detailed in Section 0, Prerequisite 5).

This is typically stored in `/home/<your_user>/.docker/config.json` on the host (e.g., `/home/yoder/.docker/config.json`). We will mount this file into the Watchtower container.

```bash
# Ensure /home/yoder/.docker/config.json exists on your host from a successful `docker login`
docker run -d --name watchtower --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  # Mount the host's Docker config file to give Watchtower access to private registry credentials
  -v /home/yoder/.docker/config.json:/config.json:ro \
  -e WATCHTOWER_CLEANUP=true \
  -e WATCHTOWER_ROLLING_RESTART=true \
  --interval 30 \
  containrrr/watchtower \
  --debug
```

(No explicit container list ⇒ it watches everything except itself and Traefik.)
*Watchtower monitors *running* containers. For a new application, you must start it once manually (see Section 4B) for Watchtower to begin managing its updates.*

---

## 7 — GitHub Actions template (build + push)

`.github/workflows/ci.yml`

```yaml
on:
  push:
    branches: [main]

jobs:
  build-push:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: registry.yosefbyd.com
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASS }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            registry.yosefbyd.com/myapi:latest
            registry.yosefbyd.com/myapi:${{ github.sha }}
```

---

## 8 — Verification cheatsheet

| Goal                    | Command                                                                     | Expected                         |
| ----------------------- | --------------------------------------------------------------------------- | -------------------------------- |
| Traefik alive           | `curl -I http://10.0.0.13/`                                                 | `404 Not Found` (Traefik banner) |
| Dashboard               | Browser → `http://10.0.0.13:8080/dashboard/`                                | UI loads                         |
| Container routed        | `curl -I -H "Host: portainer.yosefbyd.com" http://10.0.0.13/`               | `200` or `302`                   |
| Registry up             | `curl -I -H "Host: registry.yosefbyd.com" http://10.0.0.13/v2/`             | `401 Unauthorized`               |
| LAN speed test for pull | add `10.0.0.13 registry.yosefbyd.com` to `/etc/hosts`, then `docker pull …` | Full LAN speed                   |

---

## 9 — Troubleshooting map

| Symptom                     | Usual cause                                                                               | Fix                                                                                       |
| --------------------------- | ----------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| Cloudflare 502              | Wrong port/scheme in container label; container not on **proxy** network; container down. | Check `docker ps`, Traefik dashboard → *Routers*; verify `server.port` + `scheme` labels. |
| curl hangs on host :80      | UFW blocked port 80.                                                                      | `sudo ufw allow 80/tcp`                                                                   |
| Registry container restarts | Bad htpasswd file.                                                                        | Re‑create with `htpasswd -nbB` line.                                                      |
| `docker push` fails with 401 Unauthorized during blob upload (URL might show HTTP) | Registry is redirecting HTTPS client to HTTP, causing credentials to be dropped. | Ensure registry container is started with `-e REGISTRY_HTTP_RELATIVEURLS=true`. See Section 5.3. |
| Watchtower doesn't update from private registry / logs "no basic auth credentials" | Watchtower container doesn't have credentials for the private registry.                  | Mount the host's Docker `config.json` (e.g., `/home/yoder/.docker/config.json`) into the Watchtower container at `/config.json:ro`. See Section 6. |
| Dashboard 404               | `--api.insecure=true` missing **or** wrong port bound.                                    | Restart Traefik with correct flags.                                                       |
| Watchtower doesn't update (general) | Runs with explicit container list or missing perms.                                       | Launch without list; ensure `/var/run/docker.sock` mounted. Check Watchtower logs with `--debug`. |
| New service not reachable   | Forgot `traefik.enable=true` **or** defaultRule mis‑matches name.                         | Add label or override router rule.                                                        |
| `docker run <image>` on host fails with "no basic auth credentials" or "401 Unauthorized" | Docker daemon on the host is not logged into the private registry. | On the host, run `docker login registry.yosefbyd.com` and enter credentials. See Section 0. |

Check logs quickly:

```
docker logs traefik | tail
# or
docker logs <service> | tail
journalctl -u cloudflared -f
```

---

## 10 — Tidying & hardening suggestions

* Remove `-p 8080:8080` and expose dashboard via Traefik with labels:
  `-l traefik.http.routers.dash.rule=Host(`traefik.yosefbyd.com`)`  & secure with Cloudflare Access.
* For production, set `--api.insecure=false` and attach the dashboard only to the dedicated router.
* Add Prometheus & Loki exporters if you need metrics + logs.
* Use Traefik ACME to terminate TLS locally if you ever abandon Cloudflare Tunnel.

---

## Ready‑for‑audit Test

1. Laptop on LAN: `ssh yoder@10.0.0.13` works.
2. Browser (any network): `https://netdata.yosefbyd.com` works, auto‑redirects to Cloudflare Access if policy enabled.
3. **On the Docker host (`10.0.0.13`)**: `docker login registry.yosefbyd.com` succeeds (enter credentials when prompted).
4. **Initial deployment of a test application (e.g., 'mytestapp'):**
   a. Create a simple Dockerfile and GitHub Actions workflow for `mytestapp` that pushes `registry.yosefbyd.com/mytestapp:latest`.
   b. `git push` to *main* for `mytestapp` triggers GitHub Action, which builds and pushes the image.
   c. **On the Docker host**: Manually run `mytestapp` once using `docker run ...` or `docker-compose up -d ...` (as detailed in Section 4B), ensuring it uses `registry.yosefbyd.com/mytestapp:latest`.
   d. Verify `https://mytestapp.yosefbyd.com` is live.
5. **Automated update of the test application:**
   a. Make a small change to `mytestapp` (e.g., update a "Hello World" message).
   b. `git push` to *main* again. GitHub Action builds and pushes the new image.
   c. Watchtower (running on the host) detects the new image for the *already running* `mytestapp` container and updates it within ~1 minute.
   d. Verify the change is live at `https://mytestapp.yosefbyd.com`.

If **all five** pass, the stack is operational for deploying new applications and automatically updating them.

---

*End of run‑book – keep this file under version control.*
