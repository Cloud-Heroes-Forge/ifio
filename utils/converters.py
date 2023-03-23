def bandwidth_conversion(line: str) -> str:
    bandwidth: str = (line.split(','))[1].split(' ')[1].split('=')[1]
    if 'Mi' in bandwidth:
        bandwidth = bandwidth.split('M')[0]
    elif 'Ki' in bandwidth:
        bandwidth = float(bandwidth.split('K')[0]) / 2 ** 10
    elif 'Gi' in bandwidth:
        bandwidth = float(bandwidth.split('K')[0]) * 2 ** 20
    elif 'Ti' in bandwidth:
        bandwidth = float(bandwidth.split('K')[0]) * 2 ** 30
    return bandwidth


def io_conversion(line: str) -> float:
    io: float = line.split(',')[0].split('=')[1]
    if 'k' in io:
        io = int(float(io[0:-1]) * 10 ** 3)
    elif 'm' in io:
        io = int(float(io[0:-1]) * 10 ** 6)
    return io


def lat_conversion(line: str) -> float:
    lat: float = float(line.split(',')[2].split('=')[1])
    if line[5] == 'u':
        lat = lat / 10 ** 3
    elif line[5] == 'n':
        lat = lat / 10 ** 6
    elif line[5] == 's':
        lat = lat * 10 ** 3
    return lat

def average(x: int, y: int):
    return (x + y) // 2