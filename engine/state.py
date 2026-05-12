from dataclasses import dataclass

@dataclass
class FinancialState:
    age: int

    pension: float
    isa: float
    taxable: float
    cash: float

    def total_value(self) -> float:
        return self.pension + self.isa + self.taxable + self.cash