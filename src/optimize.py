import json
import random
import subprocess
import argparse

# ─── Parse seed flag ────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(
    description="Optimize trading params, with optional random seed"
)
parser.add_argument(
    "--seed",
    type=int,
    help="Seed for the RNG to make optimization reproducible"
)
args = parser.parse_args()
if args.seed is not None:
    random.seed(args.seed)
    print(f"[optimize.py] Random seed set to {args.seed}")

# Define parameter ranges
SMA_MIN, SMA_MAX = 10, 100               # SMA window range (inclusive)
TP_MIN, TP_MAX = 2.0, 10.0                # Take-profit range
SL_MIN, SL_MAX = -5.0, -0.5             # Stop-loss range (negative values)
TIMEFRAME_MIN, TIMEFRAME_MAX = 1, 20  # Time frame range in minutes (inclusive)

# Configuration: number of random combinations to try
NUM_COMBINATIONS = 500

best_profit = float("-inf")
best_params = None

for time in range(NUM_COMBINATIONS):
    # Randomly sample a combination of parameters
    sma_window = random.randint(SMA_MIN, SMA_MAX)
    take_profit = round(random.uniform(TP_MIN, TP_MAX), 2)
    stop_loss = round(random.uniform(SL_MIN, SL_MAX), 2)
    time_frame = random.randint(TIMEFRAME_MIN, TIMEFRAME_MAX)
    
    # But the total time is not more than 500 minutes for a day
    if time_frame * sma_window > 100:
        sma_window = 100 // time_frame

    params = {
        "sma_window": sma_window,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        "time_frame": time_frame
    }

    # Save parameters to params.json for use by other scripts
    with open("src/params.json", "w") as f:
        json.dump(params, f, indent=4)

    # Run data_processing.py to generate in-sample and out-sample JSON files
    try:
        subprocess.run(
            ["python", "src/data_processing.py"], 
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        # Handle errors gracefully: print error and skip this combination
        print(f"Error: data_processing.py failed for params {params} (skipping).")
        print(e.stderr)  # Print the error message for debugging
        continue
    #print("Data processing completed successfully.")
    # Run backtest.py on the in-sample data to evaluate performance
    try:
        result = subprocess.run(
            ["python", "src/backtest.py", "in-sample.json"],  # backtest reads from src/in-sample.json internally
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error: backtest.py failed for params {params} (skipping).")
        print(e.stderr)  # Print the error message for debugging
        continue

    # Parse the total profit from backtest output
    output_text = result.stdout
    total_profit = 0.0
    trades = 0
    for line in output_text.splitlines():
        if "Total Profit:" in line:
            # Expected format: "Total Profit: X VND"
            try:
                profit_str = line.split("Total Profit:")[1].strip()
                # Remove the currency and commas, convert to float
                profit_value = profit_str.replace("VND", "").strip().replace(",", "")
                total_profit = float(profit_value)
            except ValueError:
                total_profit = 0.0
        if "Total Trades:" in line:
            # Expected format: "Total trades: X"
            try:
                trades_str = line.split("Total Trades:")[1].strip()
                trades = int(trades_str)
            except ValueError:
                trades = 0
    # Run data_processing.py to generate in-sample and out-sample JSON files
    try:
        result = subprocess.run(
            ["python", "src/evaluate.py", "--optimize"], 
            check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as e:
        # Handle errors gracefully: print error and skip this combination
        print(f"Error: evaluate.py failed for params {params} (skipping).")
        print(e.stderr)  # Print the error message for debugging
        continue
    output_text = result.stdout
    sharpe = 0.0
    for line in output_text.splitlines():
        if "Daily-based Sharpe Ratio:" in line:
            # Expected format: "Daily-based Sharpe Ratio: X"
            try:
                profit_str = line.split("Daily-based Sharpe Ratio:")[1].strip()
                # Remove the currency and commas, convert to float
                profit_value = profit_str.strip().replace(",", "")
                sharpe = float(profit_value)
            except ValueError:
                sharpe = 0.0
    print(f"Set {time}: Tested params {params} => Total Profit: {total_profit} VND, "
        f"Total Trades: {trades} => Sharpe Ratio: {sharpe:.2f}")
    with open("src/optimization_results.txt", "a") as log_f:
        log_f.write(
            f"Tested params {params} => Total Profit: {total_profit} VND, "
            f"Total Trades: {trades} => Sharpe Ratio: {sharpe:.2f}\n"
        )
    # Check if this combination is the best so far
    if total_profit > best_profit and trades > 10:
        # Ensure that the number of trades is reasonable (e.g., more than 10)
        best_profit = total_profit
        best_params = params

# After testing all combinations, save the best parameters and output the result
if best_params is not None:
    with open("src/params.json", "w") as f:
        json.dump(best_params, f, indent=4)
    print(f"Best parameters: SMA window = {best_params['sma_window']}, "
        f"Take-Profit = {best_params['take_profit']}, "
        f"Stop-Loss = {best_params['stop_loss']}, "
        f"Time-Frame = {best_params['time_frame']} minutes "
        f"(Profit: {best_profit} VND)")
else:
    print("No successful parameter set found during optimization.")
