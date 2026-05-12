import numpy as np


from dataclasses import dataclass

@dataclass
class MarketReturns:
    equity: float
    bonds: float
    cash: float

def generate_returns(eq_mean=0.06, eq_vol=0.15,
                     bond_mean=0.03, bond_vol=0.05):

    equity = np.random.normal(eq_mean, eq_vol)
    bonds = np.random.normal(bond_mean, bond_vol)
    cash = 0.01  # stable nominal cash return

    return MarketReturns(equity, bonds, cash)