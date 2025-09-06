# PowerShell to Python Migration

## ✅ Complete Migration Status

All PowerShell scripts have been successfully converted to Python commands integrated into the main CLI and **moved to the `archive/` folder**.

## Command Equivalents

| Archived PowerShell Script | New Python Command | Status |
|---------------------------|-------------------|--------|
| `archive/vrf_extract_callout_models.ps1` | `cs2-callouts extract` | ✅ Complete |
| `archive/clean_outputs.ps1` | `cs2-callouts clean` | ✅ Complete |
| `archive/vrf_setup.ps1` | `cs2-callouts setup` | ✅ Complete |
| `archive/check_env.ps1` | `cs2-callouts check-env` | ✅ Complete |
| `archive/run_map.ps1` | `cs2-callouts run-map` | ✅ Complete |

## Migration Examples

### Before (PowerShell - ARCHIVED)
```powershell
# Setup
cd archive && .\vrf_setup.ps1 && cd ..

# Extract and process
cd archive && .\vrf_extract_callout_models.ps1 -Map de_mirage && cd ..
python -m cs2_callouts.cli --map de_mirage

# Clean up
cd archive && .\clean_outputs.ps1 -Confirm:$false && cd ..

# Check environment
cd archive && .\check_env.ps1 -Names @("VAR1", "VAR2") && cd ..
```

### After (Python)
```bash
# Setup
cs2-callouts setup

# Extract and process (single command)
cs2-callouts pipeline --map de_mirage

# Or step by step
cs2-callouts extract --map de_mirage
cs2-callouts process --map de_mirage

# Clean up
cs2-callouts clean                        # Removes everything including tools

# Or if you want to keep tools to avoid re-downloading
cs2-callouts clean --exclude-tools

# Check environment
cs2-callouts check-env --names VAR1 VAR2
```

## Benefits of Python Migration

1. **Cross-Platform**: Works on Windows, Linux, macOS
2. **Unified Codebase**: Everything in Python
3. **Better Error Handling**: Proper exception management
4. **Package Integration**: Installable as a proper Python package
5. **Consistent CLI**: All commands under one interface
6. **Enhanced Features**: More robust path handling and validation

## Backward Compatibility

The PowerShell scripts have been **moved to the `archive/` folder** and are considered **deprecated**. They are retained for:

1. **Reference purposes** - Understanding the original implementation
2. **Emergency fallback** - Windows-only backup option
3. **Documentation** - Migration process history

**⚠️ Important**: PowerShell scripts may be **removed in a future version**. All new development should use the Python CLI commands.

## File Structure After Migration

```
CS2Callouts/
├── cs2_callouts/           # Python package
├── archive/                # Archived PowerShell scripts (DEPRECATED)
│   ├── README.md          # Archive documentation
│   ├── vrf_extract_callout_models.ps1
│   ├── clean_outputs.ps1
│   ├── vrf_setup.ps1
│   ├── check_env.ps1
│   └── run_map.ps1
├── README.md              # Updated documentation
├── MIGRATION.md           # This file
└── scripts.py             # Python utility entry point
```

## Installation

```bash
# Install as editable package
pip install -e .

# Now all commands are available as:
cs2-callouts <command>
```

Or use without installation:
```bash
python -m cs2_callouts.cli <command>
```
