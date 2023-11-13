# CS587 Github Dashboard

This is a GitHub dashboard made for our CS587 class

Both the Django web server and postgreSQL database are hosted on Render.com

The website is hosted live at [cs587-dashboard.onrender.com](https://cs587-dashboard.onrender.com)

## Deploying

The included docker file runs the webserver, however, the postgreSQL server has to be setup separately. If a database is not setup, repositories will not be cached.

The environment variables are as follows.

```properties
# Github OAuth App authentication
GITHUB_OAUTH_SECRET=********
GITHUB_OAUTH_CLIENT_ID=********

# Django secret key
SECRET_KEY=********

# Bypass authentication with a GitHub personal token (Defaults to OAuth app behavior, uncomment to use)
# CURRENT_TOKEN=********

# Invalidate repo cache after x seconds (uncomment to set, defaults to 1hr)
# CACHE_INVALIDATE=3600

# Setup connection info for the database (Uncomment to use)
# DB_ENGINE=postgresql
# DB_USERNAME=postgres
# DB_PASS=1234
# DB_HOST=127.0.0.1
# DB_PORT=5432
# DB_NAME=cs587_dashboard_db

# Alternatively, use a URL, example is shown (Uncomment to use)
# DB_URL=postgres://cs587_dashboard_db_user:*********@dpg-******-a.oregon-postgres.render.com/cs587_dashboard_db
```

If no environment variables are set, the app should run, but logging in will not work.
