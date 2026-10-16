from pharmachain.domain.state import LedgerState
from pharmachain.engines.educational.adapter import EducationalHotStuffAdapter

engine = EducationalHotStuffAdapter(LedgerState({}))

print(engine.name)
print(engine.snapshot())
