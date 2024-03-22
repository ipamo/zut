Tips
====

## Quick start guide for development

Create Python virtual environment (example for Windows):

    python -m venv .venv      # Debian: python3 -m venv .venv
    .\.venv\Scripts\activate  # Linux:  source .venv/bin/activate
    python -m pip install --upgrade pip wheel setuptools
    pip install -r requirements.txt

Create postgresql test database (example):

    createdb -U postgres --encoding UTF-8 --locale en_US.UTF8 --template template0 test_zut

Configure tests with a `data/tests.conf` file (see [example](https://ipamo.net/zut/latest/_static/examples/tests.conf)).

Run tests:

    python test.py


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
