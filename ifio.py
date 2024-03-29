# autofio.py 
# wrapper around the fio tool to automate the process of finding the optimal IO depth

import os
import sys
import json
import pandas as pd
from typing import List, Dict
from utils.models import FioBase, FioOptimizer
from utils.parsers import parse_fio_config
from argparse import ArgumentParser, Namespace
from reporting import pgreports
from datetime import datetime
import matplotlib.pyplot as plt
import logging

def arg_parser_setup() -> Namespace:
    logging.info("Parsing Arguments")
    parser = ArgumentParser(description="Optimizer for fio")
    parser.add_argument('-v', '--verbose',
                        action='store_true', help="Displays verbose output")
    parser.add_argument('-bs', '--blocksize', nargs='+', default=["8K,randrw"], 
                        help='Block Sizes,[randrw/rw] to test. Defaults to 8K,randrw. ' +
                            'Append ,rw to specify sequential IO and ,randrw for random IO. ' +
                            'For multiple block sizes use -bs 8K,randrw 32K,rw 64K,rw')
    parser.add_argument('-rw', '--readpercentages', nargs='+', default=["0", "25", "50", "75", "100"],
                        help='Read Percentage to test. Defaults to 0 25 50 75 100, for multiple read percentages use -rw 0 10 20 30 40')
    # region advanced options
    parser.add_argument('-c', '--config', default='fio.ini',
                        help='path to config file. Defaults to fio.ini')
    parser.add_argument('-e', '--email', nargs='+', 
                        action='append', help='list of emails to send notifications, defaults is none')
    parser.add_argument('-tw', '--throughputweight', type=int, default=1,
                        help='Weight of Throughput for ATP calculation. Defaults to 1')
    # endregion advanced options
    parser.add_argument('-n', '--name', default="fio-test", help="Name of the fio job(s). Defaults to job1")
    args = parser.parse_args()
    logging.debug(f"Arguments: {args}")
    return args

def save_single_output(fio_opt: FioOptimizer, timestamp: datetime) -> None:
    """
    
    """
    output_folder: str = os.path.join(os.getcwd(), f'output/ifio_{timestamp}', f'/{fio_opt.config["bs"]}_{fio_opt.config["rw"]}_{fio_opt.config["rwmixread"]}')
    logging.debug(f"Saving output to {output_folder}")
    try:
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        fio_optimizer_df = fio_opt.to_DataFrame()
        logging.debug(fio_optimizer_df.head())
        logging.info(f"Saving csv to {output_folder}/fio.csv")
        fio_optimizer_df.to_csv(f'{output_folder}/fio.csv')
        logging.info(f"Saving Raw Output to {output_folder}/raw.json")
        with open(f'{output_folder}/raw.json', 'w') as f:
            json.dump(fio_opt.runs_raw, f)
        fig: plt.Figure = pgreports.generate_single_run_graphs(fio_optimizer_df)
        # plt.plot(figure=fig)
        fig.savefig(f'{output_folder}_queueDepthChart.png')

    except json.JSONDecodeError as jde:
        logging.debug(f'failed to save results: {jde}')

def save_summary_output(results: Dict[tuple, FioOptimizer], timestamp: datetime) -> None:
    logging.info("Saving Summary Output")
    output_folder: str = os.path.join(os.getcwd(), 
                                      f'output/ifio_{timestamp}')
    if not os.path.exists(output_folder):
        os.makedirs(output_folder, exist_ok=True)
    combined_results: pd.DataFrame = pd.DataFrame()
    # best_runs: Dict[str, FioBase] = {}
    best_runs_df: pd.DataFrame = pd.DataFrame()
    for key, value in results.items():
        data = value.to_DataFrame().reset_index()
        data['blocksize'] = key[0]
        data['rw'] = key[1]
        combined_results = combined_results.append(data)
        best_runs_df = best_runs_df.append(value.best_run.to_dict(), ignore_index=True)

    # # print(run.to_dict())
    # best_runs_df['blocksize'] = best_runs_df['blocksize'].astype(str)
    # best_runs_df['rw'] = best_runs_df['rw'].astype(str)
    # best_runs_df['rwmixread'] = best_runs_df['rwmixread'].astype(str)
    logging.info(f"Saving combined csv to {output_folder}.csv")
    combined_results.to_csv(f'{output_folder}.csv')
    
    for blocksize, blocksize_df in best_runs_df.groupby('blocksize'):
        fig: plt.Figure = pgreports.generate_rwmix_stacked_graphs(blocksize_df)
        if not os.path.exists(output_folder):
            os.makedirs(output_folder, exist_ok=True)
        fig.savefig(f'{output_folder}/{blocksize}_{blocksize_df["read_percent"].values[0]}.png')
    
    # pgreports.generate_fio_report(combined_results, output_folder)



def main():
    args = arg_parser_setup()
    logging.basicConfig(format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%dT%H:%M:%S', 
                        level=logging.INFO,
                        handlers=[
                            logging.FileHandler("autofio.log", mode='w+'),
                            logging.StreamHandler(sys.stdout)
                        ]
    )
    args = arg_parser_setup()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.debug("Verbose Output Enabled")
        logging.debug(f"Arguments: {args}")

    
    values_to_test: list = []
    results: dict = {}
    blocksizes = args.blocksize
    if len(blocksizes) == 1: 
        blocksizes = blocksizes[0].split(" ")
    for blocksize in blocksizes:
        read_percentages = args.readpercentages
        if len(read_percentages) == 1:
            read_percentages = read_percentages[0].split(" ")
        for read_percentage in read_percentages:
            bs = blocksize.split(',')[0]
            rw = blocksize.split(',')[1] if len(blocksize.split(',')) > 1 else 'randrw'
            values_to_test.append((bs, rw, read_percentage))
    logging.info(f'Total Values to Test: {len(values_to_test)}')
    logging.debug(f'Values to Test: {values_to_test}')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for index, values in enumerate(values_to_test):
        logging.info(f"Starting {index+1} of {len(values_to_test)}:  {values[0]} {values[1]} {values[2]} ")
        fio_optimizer: FioOptimizer = FioOptimizer()
        
        # read the config file and parse it into a dictionary with ConfigParser
        parsed_config: dict = parse_fio_config(args.config)
        logging.debug(f"Parsed Config: {parsed_config}")
        fio_optimizer.config = parsed_config
        
        # set other attributes
        fio_optimizer.config['bs'] = values[0]
        fio_optimizer.config['rw'] = values[1]
        fio_optimizer.config['rwmixread'] = values[2]
        fio_optimizer.min = 1
        fio_optimizer.max = 65536
        fio_optimizer.throughputweight = args.throughputweight if args.throughputweight > 0 else 1

        logging.debug(f"Optimizer Config: {fio_optimizer.config}")
        fio_optimizer.find_optimal_iodepth()

        save_single_output(fio_optimizer, timestamp)
        results[values] = fio_optimizer
        logging.info(f"Finished {index+1} of {len(values_to_test)}:  {values[0]} {values[1]} {values[2]} ")
        logging.info(f"##################################################")

    save_summary_output(results, timestamp)
        

        

if __name__ == '__main__':
    main()

