"""GDGuard: Godot-native project validation and CI checks."""

__version__ = "0.1.0"

from gdguard.models import CheckResult, ScanReport, Status

__all__ = ["CheckResult", "ScanReport", "Status", "__version__"]
