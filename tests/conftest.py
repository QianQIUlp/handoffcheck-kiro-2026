import sys
from pathlib import Path

# Add skills/check-handoff/scripts to path for core imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'skills' / 'check-handoff' / 'scripts'))
