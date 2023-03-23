import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import jinja2

def generate_total_throughput_chart(data: pd.DataFrame) -> plt.Figure:
    fig, ax1 = plt.subplots()

    # plot total throughput on the left y-axis
    ax1.bar(np.arange(len(data['total_throughput'])), data['total_throughput'], color='tab:blue')
    ax1.set_ylabel('Total Throughput', color='tab:blue')
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.set_xticks(np.arange(len(data['total_throughput'])))
    ax1.set_xticklabels(data['xlabels'], rotation=90)

    # plot average latency on the right y-axis
    ax2 = ax1.twinx()
    ax2.plot(np.arange(len(data['avg_latency'])), data['avg_latency'], color='tab:orange')
    ax2.set_ylabel('Average Latency (ms)', color='tab:orange')
    ax2.tick_params(axis='y', labelcolor='tab:orange')

    plt.title('Total Throughput vs Blocksize')
    plt.tight_layout()
    return fig

def generate_rwmix_stacked_graphs(data: pd.DataFrame) -> plt.Figure:
    """
    Generates a stacked graph of read and write throughput for each blocksize.
    """
    
    fig, (ax1, ax2) = plt.subplots(nrows=2, figsize=(8, 8), gridspec_kw={'height_ratios': [1, 1]})
    # Create stacked (read and write) throughput graph for each blocksize on ax1
    ax1.bar(x=data['read_percent'], height=data['read_throughput'], label='Read', color='blue', width=10)
    ax1.bar(x=data['read_percent'], height=data['write_throughput'], label='Write', color='orange', width=10, bottom=data['read_throughput'])
    # add a comment to the graph for total throughput on each bar
    for i in range(len(data['read_percent'])):
        ax1.annotate(f"{data['total_throughput'].values[i]:.0f} KiB/s",
                xy=(data['read_percent'].values[i], data['total_throughput'].values[i]),
                xytext=(data['read_percent'].values[i], data['total_throughput'].values[i] + 100)
    )
    ax1.set_xticks(data['read_percent'])
    ax1.set_xlabel('Read Percentage')
    ax1.set_xticklabels(data['read_percent'])
    ax1.set_ylabel('Throughput (KiB/s)')
    ax1.legend()

    # Create line chart with avg_latency on right axis and total iops on left axis
    ax2.plot(data['read_percent'], data['avg_latency'], label='Avg Latency', color='blue')
    ax2.set_ylabel('Avg Latency (ms)')
    ax2.set_xlabel('Read Percentage')
    ax2.set_xticks(data['read_percent'])
    ax2.set_xticklabels(data['read_percent'])
    ax2.set_ylim(0, data['avg_latency'].max() * 1.1)
    ax2.legend(loc='upper left')
    ax3 = ax2.twinx()
    ax3.plot(data['read_percent'], data['total_iops'], label='Total IOPS', color='orange')
    ax3.set_ylabel('Total IOPS')
    ax3.set_ylim(0, data['total_iops'].max() * 1.1)
    ax3.legend(loc='upper right')
    return fig


def generate_fio_report(data: pd.DataFrame, report_file_path: str) -> None:
    """Using the template.html file, generates an html report for the fio results.
        * overall summary of all of the `blocksize` parameters together
        * one page with 2 charts showing:
            ** y axis: Total Throughput, x axis: Blocksize, secondary y axis: avg_latency
            ** y axis: Total IOPS, x axis: Blocksize, secondary y axis: avg_latency
        * for each `blocksize`: 
            ** a paragraph summary 
            ** charts showing:
                *** y axis: Total Throughput, x axis: io_depth, secondary y axis: avg_latency
                *** y axis: Total IOPS, x axis: io_depth, secondary y axis: avg_latency
    Args:
        fio_results (pd.DataFrame): list of fio results
        report_file_path (str): path to report file

    Returns:
        None
    """
    # load the template
    template_loader = jinja2.FileSystemLoader(searchpath="./")
    template_env = jinja2.Environment(loader=template_loader)
    template = template_env.get_template("template.html")

    # build Summaries and Graphs
    
    generate_total_throughput_chart(data).savefig('images/total_throughput.png')



    # generate the report
    report = template.render(
        overall_summary=overall_summary,
        total_throughput_chart='images/total_throughput.png'
    )

    # write the report to a file
    with open(report_file_path, 'w') as f:
        f.write(report)
   