Tips
====

## Quick start guide for development

Install required dependencies (example on Debian Linux):

- For mssql:

    curl https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
    echo "deb https://packages.microsoft.com/debian/12/prod bookworm main" | sudo tee /etc/apt/sources.list.d/mssql.list
    sudo apt-get update
    sudo ACCEPT_EULA=Y apt-get install msodbcsql18 mssql-tools18

- For mysql:

    sudo apt-get install python3-dev default-libmysqlclient-dev build-essential

Create Python virtual environment (example on Debian Linux):

    python3 -m venv .venv       # Windows:  python -m venv .venv
    source .venv/bin/activate   # Windows:  .\.venv\Scripts\activate
    python -m pip install --upgrade pip wheel setuptools
    pip install -r requirements.txt

Create postgresql test database (example):

    createdb -U postgres --encoding UTF-8 --locale en_US.UTF8 --template template0 test_zut

Configure tests with a `data/tests.conf` file (see [example](https://ipamo.net/zut/latest/_static/examples/tests.conf)).

Start test databases using Docker:

- MssqlAdapter :
    
    docker run -d --rm --name zut-tests-mssql -e ACCEPT_EULA=Y -e MSSQL_SA_PASSWORD=testmeZ0 -e MARIADB_DATABASE=test_zut -e TZ=Europe/Paris -p 127.0.0.1:1433:1433 mcr.microsoft.com/mssql/server:2022-latest
    docker exec -it zut-tests-mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P testmeZ0 -Q "CREATE DATABASE TestZut"

- MysqlAdapter :
    
    docker run -d --rm --name zut-tests-mysql -e MARIADB_ROOT_PASSWORD=testmeZ0 -e MARIADB_DATABASE=test_zut -e TZ=Europe/Paris -p 127.0.0.1:3306:3306 mariadb

- PgAdapter :
    
    docker run -d --rm --name zut-tests-pg -e POSTGRES_PASSWORD=testmeZ0 -e POSTGRES_DB=test_zut -e TZ=Europe/Paris -p 127.0.0.1:5432:5432 postgres

Run tests:

    python -m unittest


## Install from a git repository

From a Git branch or tag (using https or ssh):

    pip install git+https://github.com/ipamo/zut.git@main#egg=zut
    pip install git+ssh://git@github.com/ipamo/zut.git@main#egg=zut


## Clean repository

Using Powershell:

```ps1
Get-ChildItem -Include __pycache__,build,*.egg-info -Recurse -force | Where-Object fullname -notlike "*\.venv\*" | Remove-Item -Force -Recurse
```

Using Linux shell:

```sh
find . \( -name __pycache__ -o -name build -o -name "*.egg-info" \) -not -path "./.venv/*" -exec rm -rf {} \;
```

View non-versionned files:

    git ls-files -o -x .venv
