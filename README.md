Zut
===

Reusable Python utilities.


## Installation

Zut package is published [on PyPI](https://pypi.org/project/zut/):

```sh
pip install zut
```


## Usage examples

See also [full documentation](https://ipamo.net/zut) (including [API reference](https://ipamo.net/zut/latest/api-reference.html)).


### Configure logging

```py
from zut import configure_logging
configure_logging()
```

### Flexible output

Write text or tabular data to a flexible, easily configurable output: CSV or Excel file, or tabulated stdout/stderr.

The output file may be on the local file system or on a Windows/Samba share (including when the library is used on Linux).

Export text to stdout or to a file:

```py
import sys
from zut import out_file

with out_file(filename or sys.stdout) as f:
    f.write("Content")
```
    
Export tabular data to stdout or to a file:

```py
import sys
from zut import out_table

with out_table(filename or sys.stdout, headers=["Id", "Word"]) as t:
    t.append([1, "Hello"])
    t.append([2, "World"])
```

Tabular data can also be exported using dictionnaries (in this case, headers will be detected automatically by the library):

```py
import sys
from zut import out_table

with out_table(filename or sys.stdout) as t:
    t.append({'id': 1, 'name': "Hello"})
    t.append({'id': 2, 'col3': True})
```

If `filename` has extension with `.xlsx`, output will be in Excel 2010 format.
Otherwise it will be in CSV format.

If `filename` starts with `\\`, output will be done on the corresponding Windows/Samba share.
To indicate Samba credentials, call `configure_smb_credentials` before using function `out_table`.
Example:

```py
from zut import out_table, configure_smb_credentials

configure_smb_credentials(user=..., password=...)

with out_table(r"\\server\share\path\to\file") as o:
    ...
```


## Legal

This project is licensed under the terms of the [MIT license](https://raw.githubusercontent.com/ipamo/zut/main/LICENSE.txt).
