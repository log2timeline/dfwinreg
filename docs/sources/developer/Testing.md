# Testing

## Unit tests

The dfwinreg package comes with automated tests. These tests are stored in the
`tests` subdirectory.

To run the automated tests:

```bash
PYTHONPATH=. python run_tests.py
```

Or on Windows:

```bash
set PYTHONPATH=.
C:\Python3\python.exe run_tests.py
```

If you're running git on Windows make sure you have autocrlf turned off
otherwise the tests using the test text files will fail.

```bash
git config --global core.autocrlf false
```
