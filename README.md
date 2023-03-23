# Autofio.py

Autofio.py is a Python script that automates the process of running disk storage performance tests using the `fio` package. It allows users to easily specify block sizes, read percentages, and other parameters to test, and generates a set of reports with the results.

## Requirements

Autofio.py requires the `fio` package to be installed on the system.

## Usage

To use autofio.py, simply run the script with the desired parameters. The following command-line arguments are available:

- `-h, --help`: Displays help message and exits.
- `-v, --verbose`: Displays verbose output.
- `-bs BLOCKSIZE [BLOCKSIZE ...], --blocksize BLOCKSIZE [BLOCKSIZE ...]`: Block sizes and IO types to test. Defaults to `"8K,randrw"`. For multiple block sizes, use the format `"BLOCKSIZE,IO_TYPE BLOCKSIZE,IO_TYPE"`.
- `-rw READPERCENTAGES [READPERCENTAGES ...], --readpercentages READPERCENTAGES [READPERCENTAGES ...]`: Read percentages to test. Defaults to `"50"`. For multiple read percentages, use the format `"READ_PERCENTAGE READ_PERCENTAGE"`.
- `-c CONFIG, --config CONFIG`: Path to the fio configuration file. Defaults to `"fio.ini"`.
- `-e EMAIL [EMAIL ...], --email EMAIL [EMAIL ...]`: List of email addresses to send notifications to. Defaults to an empty list.
- `-tw THROUGHPUTWEIGHT, --throughputweight THROUGHPUTWEIGHT`: Weight of throughput for ATP calculation. Defaults to `1`.
- `-n NAME, --name NAME`: Name of the fio job(s). Defaults to `"job1"`.

For example, to test with block sizes of 8K and 32K, and read percentages of 0, 25, 50, 75, and 100, run the following command:

```
python autofio.py -bs "8K,randrw 32K,rw" -rw "0 25 50 75 100"
```

## Output

Autofio.py generates a report with the results of the performance tests. The report includes the following information:

- Block size and IO type
- Read percentage
- Average throughput
- Average IOPS
- Average latency
- ATP (Application Throughput Performance) score, calculated using the half-latency rule from the paper "Half-Latency Rule for Finding the Knee of the Latency Curve" by Naresh M. Patel found here: http://www.cs.cmu.edu/~naresh/papers/latency.pdf


The report is saved to an output folder in the same directory as the script.