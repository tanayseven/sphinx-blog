### To perform local setup

### Create virtual environment and install all the necessary dependencies
```shell
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Build a pure Python package

```shell
python setup.py build.py
```

### Build a package that will be uploaded to PyPI

```shell
rm -rf dist bulid
python setup.py bdist_wheel
```

### To publish a package from local

```shell
twine check dist/*
twine upload dist/*
```
