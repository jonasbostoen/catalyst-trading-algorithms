import pandas as pd
import MA_crossover_strategy
from catalyst import run_algorithm

if __name__ == "__main__":
    run_algorithm(
            capital_base = 1000,
            data_frequency = "minute",
            initialize = MA_crossover_strategy.initialize,
            handle_data = MA_crossover_strategy.handle_data,
            analyze = MA_crossover_strategy.analyze,
            exchange_name = "bitfinex",
            algo_namespace = MA_crossover_strategy.NAMESPACE,
            base_currency= "usd",
            start = pd.to_datetime("2018-4-25", utc = True),
            end = pd.to_datetime("2018-4-26", utc = True)
    )
