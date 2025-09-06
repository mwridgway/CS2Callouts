# Archived PowerShell Scripts

This folder contains the original PowerShell scripts that have been **deprecated** and replaced with Python CLI commands.

## Status: DEPRECATED ⚠️

All scripts in this folder have been converted to Python and integrated into the main CLI. **These scripts are no longer maintained and may be removed in future versions.**

## Script Migration Map

| Archived Script | Python Replacement | Status |
|----------------|-------------------|--------|
| `vrf_extract_callout_models.ps1` | `cs2-callouts extract` | ✅ Fully replaced |
| `clean_outputs.ps1` | `cs2-callouts clean` | ✅ Fully replaced |
| `vrf_setup.ps1` | `cs2-callouts setup` | ✅ Fully replaced |
| `check_env.ps1` | `cs2-callouts check-env` | ✅ Fully replaced |
| `run_map.ps1` | `cs2-callouts run-map` | ✅ Fully replaced |

## Migration Guide

### Before (PowerShell - DEPRECATED)
```powershell
.\vrf_extract_callout_models.ps1 -Map de_mirage
.\clean_outputs.ps1 -Confirm:$false
```

### After (Python - CURRENT)
```bash
cs2-callouts pipeline --map de_mirage
cs2-callouts clean
```

## Why These Scripts Were Archived

1. **Cross-Platform Compatibility**: Python works on Windows, Linux, macOS
2. **Unified Codebase**: Everything now in one language
3. **Better Error Handling**: More robust exception management
4. **Enhanced Features**: Improved functionality and validation
5. **Easier Maintenance**: Single codebase to maintain

## When Will These Be Deleted?

These scripts will be removed in a future version once the Python migration is confirmed stable. For now, they're preserved for:
- Reference purposes
- Emergency fallback (Windows only)
- Documentation of the migration process

## Migration Help

See the main [MIGRATION.md](../MIGRATION.md) file for detailed conversion examples and the complete migration guide.

---

**⚠️ Important**: Do not use these scripts for new projects. Use the Python CLI commands instead.
