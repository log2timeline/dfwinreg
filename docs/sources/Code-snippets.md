# Code snippets

## Windows Registry

To open a specific Windows Registry key from a specific Windows Registry file:

```python
from dfwinreg import registry
from winreg_kb import collector

filename = 'NTUSER.DAT'

collector_object = collector.WindowsVolumeCollector()
collector_object.GetWindowsVolumePathSpec(filename)

registry_file_reader = collector.CollectorRegistryFileReader(collector_object)
win_registry = registry.WinRegistry(registry_file_reader=registry_file_reader)
```

## Windows Registry keys
### Retrieving a key by its path

```python
key_path = 'HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion'

registry_key = win_registry.GetKeyByPath(key_path)
```

## Iterating the subkeys

```python
for subkey in registry_key.GetSubkeys():
    print subkey.name
```
