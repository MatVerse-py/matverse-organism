"""Allow `python -m matverse ...`."""
from .cli import main
import sys
sys.exit(main())
