# ifio.py

ifio.py is a Python script that automates the process of running storage performance tests using the `fio` package. It allows users to easily specify any number of  block sizes, read percentages, and other parameters to test, and generates a set of reports with the results. 

This automatically determines the queue depth for each test, taking the guess work out for you. The script also generates and saves graphical reports as well as results in both json and csv when the tests are complete.

All without the need for additional scripts to wrap around fio!

## Requirements

ifio.py requires the `fio` package to be installed on the system.

I recommend fio version >3.3 due to potential inflated write performance as detailed here - https://www.n0derunner.com/fio-versions-3-3-may-show-inflated-random-write-performance/

## Installation

To install ifio.py, simply clone the repository to your system, install fio and the python packages listed in `requirements`.

```bash
git clone git@github.com:Cloud-Heroes-Forge/ifio.git
yum install fio
pip install -r requirements
```

## Usage

To use ifio.py, simply run the script with the desired parameters. 

Most configuration options should be specified in `fio.ini` (specified with `-c filename.ini` if using anything other than fio.ini).  An example [fio.ini](fio.ini) is included in this repo for settings such as directories/files, which ioengine to use, runtime and number of jobs. 

The following command-line arguments are available:

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
python ifio.py -bs 8K,randrw 32K,rw -rw 0 25 50 75 100
```

## Output

ifio.py generates a report with the results of the performance tests. The report includes the following information:

- Block size and IO type
- Read percentage
- Average throughput
- Average IOPS
- Average latency
- ATP (Accelerated Throughput Power) score, calculated using the half-latency rule from the paper "Half-Latency Rule for Finding the Knee of the Latency Curve" by Naresh M. Patel found here: https://dl.acm.org/doi/abs/10.1145/2825236.2825248


The report is saved to an output folder in the same directory as the script.
