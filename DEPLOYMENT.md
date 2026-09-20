# Hosting preparation

**Status: prepared, not deployed.** A hosting account and storage choice are still needed.

The supplied Dockerfile packages Flask with Gunicorn. It deliberately uses one worker for this small SQLite app. Configure a persistent writable disk at `/data`; ensure the container's `wallet` user can write to the mounted directory. Use one running instance, since independent SQLite disks would produce separate copies of your records.

Set a stable randomly generated `SECRET_KEY` through your host's secret settings. Set `PORT` if the host requires a different port; the default is 8080. `DATABASE_PATH` defaults to `/data/wallet.sqlite3` in Docker and can be overridden. The host must provide HTTPS.

Before a live release, choose the audience. The existing application has no login and one shared database. It should sit behind host-level access protection for private use, or be deliberately treated as a shared demonstration with fictional entries. Anyone with access can read, edit and delete that database's records.

The local Python setup remains unchanged. Docker is optional for running the college project locally.

Container build command (Docker required):

```sh
docker build -t campus-wallet .
```

This container has not yet been built or tested in this environment. After selecting the host, the remaining steps are to configure storage and access, deploy, and verify expense persistence across a service restart.

Server configuration follows the [official Flask Gunicorn guidance](https://flask.palletsprojects.com/en/stable/deploying/gunicorn/).
