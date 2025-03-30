import numpy as np
from qiskit import *
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit.circuit.library import MCMT
from qiskit.visualization import circuit_drawer
from qiskit.visualization import matplotlib as qiskit_matplotlib
import io
import base64
import matplotlib
from qiskit.providers.aer import QasmSimulator
from optimization import optimization
matplotlib.use('Agg')


def power_of_2(n):
    return n > 0 and (n & (n - 1)) == 0


def argumentation(s):
    power = 0
    while 2 ** power < len(s):
        power += 1
    number = 2 ** power - len(s)
    k = ''
    for i in range(number):
        k = k + "$"
    return s + k


def encode(s, coding):
    ret = ''
    for each in s:
        ret += coding[each]
    return ret


def once(circuit, index_count, seps, N, pattern_string):
    re = []
    ## Cyclic shift
    for index in range(index_count):
        interval = 2 ** index * seps
        swap_interval = 0
        while 2 ** swap_interval < N * seps / interval:
            begin = 2 ** swap_interval
            temp_sep = 2 ** (swap_interval + 1)
            swap_sep = 2 ** swap_interval
            tail = (begin - 1) * interval + 1
            while tail < N * seps:
                for j in range(interval):
                    real_a = index_count + tail + j - 1
                    real_b = index_count + tail + j + swap_sep * interval - 1
                    circuit.cswap(index, real_a, real_b)
                    re.append(('cswap', index, real_a, real_b))
                tail += temp_sep * interval
            circuit.barrier()
            re.append(('barrier', 0))
            swap_interval += 1

    ## Comparsion
    for each in range(len(pattern_string)):
        circuit.cnot(index_count + each, index_count + seps * N + each)
        re.append(('cnot', index_count + each, index_count + seps * N + each))

    circuit.barrier()
    re.append(('barrier', 0))

    ## Opposite
    for each in range(len(pattern_string)):
        circuit.x(index_count + seps * N + each)
        re.append(('x', index_count + seps * N + each))

    # for each in range(len(pattern_string) - 1):
    #     circuit.cz(index_count + seps * N + each, index_count + seps * N + each + 1)
    mcz = MCMT('z', num_ctrl_qubits=len(pattern_string) - 1, num_target_qubits=1, label='MCZ')
    bits = [index_count + seps * N + each for each in range(len(pattern_string))]
    circuit.append(mcz, bits)

    i = len(re) - 1
    while i >= 0:
        opt = re[i]
        if opt[0] == 'x':
            circuit.x(opt[1])
        if opt[0] == 'cnot':
            circuit.cnot(opt[1], opt[2])
        if opt[0] == 'cswap':
            circuit.cswap(opt[1], opt[2], opt[3])
        if opt[0] == 'barrier':
            circuit.barrier()
        i -= 1

    ## diffusion
    circuit.barrier()
    for each in range(index_count):
        circuit.h(each)
        circuit.x(each)
    mcz = MCMT('z', num_ctrl_qubits=index_count - 1, num_target_qubits=1, label='MCZ')
    bits = [each for each in range(index_count)]
    circuit.append(mcz, bits)
    for each in range(index_count):
        circuit.x(each)
        circuit.h(each)
    return circuit


def generate_circuit(target_string, pattern_string):
    N = len(target_string)
    M = len(pattern_string)

    coding = None
    seps = 0

    if power_of_2(N):
        coding = {"A": "00", "C": "01", "G": "10", "T": "11"}
        seps = 2
    else:
        coding = {"A": "000", "C": "001", "G": "010", "T": "011", "$": "100"}
        seps = 3
        target_string = argumentation(target_string)
        N = len(target_string)


    target_string = encode(target_string, coding)
    pattern_string = encode(pattern_string, coding)

    index_count = 0
    while 2 ** index_count < N:
        index_count += 1

    circuit = QuantumCircuit(index_count + seps * (N + M), index_count)

    ## Initialize
    for each in range(index_count):
        circuit.h(each)

    for each in range(len(target_string)):
        if target_string[each] == "1":
            circuit.x(index_count + each)

    for each in range(len(pattern_string)):
        if pattern_string[each] == "1":
            circuit.x(index_count + seps * N + each)

    circuit.barrier()

    repeat = 1
    for ii in range(repeat):
        circuit = once(circuit, index_count, seps, N, pattern_string)

    circuit.barrier()
    for each in range(index_count):
        circuit.measure(each, each)

    img = circuit_drawer(circuit, output='mpl', fold=1000000)
    buffered = io.BytesIO()
    img.savefig(buffered, format="PNG", bbox_inches='tight')
    plt.close('all')

    # 将字节流编码为 Base64 字符串
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    qasm_str = circuit.qasm()
    return img_str, qasm_str


def once_optimized(circuit, index_count, seps, M, pattern_string, ST):
    re = []
    ## Cyclic shift
    optimized_cyc = optimization(ST, index_count)
    for opt in optimized_cyc:
        if opt[0] == 'x':
            circuit.x(opt[1])
            # continue
        if opt[0] == 'cnot':
            circuit.cnot(opt[1], opt[2])
        if opt[0] == 'cswap':
            circuit.cswap(opt[1], opt[2], opt[3])
        if opt[0] == 'barrier':
            circuit.barrier()
        if opt[0] == 'cx':
            circuit.cx(opt[1], opt[2])
        if opt[0] == 'mcx':
            circuit.mcx(opt[1], opt[2])
        re.append(opt)
    circuit.barrier()
    re.append(('barrier', 0))

    ## Comparsion
    for each in range(len(pattern_string)):
        circuit.cnot(index_count + each, index_count + seps * M + each)
        re.append(('cnot', index_count + each, index_count + seps * M + each))

    circuit.barrier()
    re.append(('barrier', 0))

    ## Opposite
    for each in range(len(pattern_string)):
        circuit.x(index_count + seps * M + each)
        re.append(('x', index_count + seps * M + each))

    mcz = MCMT('z', num_ctrl_qubits=len(pattern_string) - 1, num_target_qubits=1, label='MCZ')
    bits = [index_count + seps * M + each for each in range(len(pattern_string))]
    circuit.append(mcz, bits)

    i = len(re) - 1
    while i >= 0:
        opt = re[i]
        if opt[0] == 'x':
            circuit.x(opt[1])
        if opt[0] == 'cnot':
            circuit.cnot(opt[1], opt[2])
        if opt[0] == 'cswap':
            circuit.cswap(opt[1], opt[2], opt[3])
        if opt[0] == 'barrier':
            circuit.barrier()
        if opt[0] == 'cx':
            circuit.cx(opt[1], opt[2])
        if opt[0] == 'mcx':
            circuit.mcx(opt[1], opt[2])
        i -= 1

    ## diffusion
    circuit.barrier()
    for each in range(index_count):
        circuit.h(each)
        # circuit.z(each)
        circuit.x(each)

    mcz = MCMT('z', num_ctrl_qubits=index_count - 1, num_target_qubits=1, label='MCZ')
    bits = [each for each in range(index_count)]
    circuit.append(mcz, bits)

    for each in range(index_count):
        circuit.x(each)
        circuit.h(each)
    return circuit


def generate_optimized_circuit(target_string, pattern_string):
    N = len(target_string)
    M = len(pattern_string)

    coding = None
    seps = 0

    if power_of_2(N):
        coding = {"A": "00", "C": "01", "G": "10", "T": "11"}
        seps = 2
    else:
        coding = {"A": "000", "C": "001", "G": "010", "T": "011", "$": "100"}
        seps = 3
        target_string = argumentation(target_string)
        N = len(target_string)

    target_string = encode(target_string, coding)
    pattern_string = encode(pattern_string, coding)

    index_count = 0
    while 2 ** index_count < N:
        index_count += 1

    ST_length = seps * M
    ST = []
    temp_target_string = target_string + target_string
    for each in range(2 ** index_count):
        ST.append(str(temp_target_string[each * seps: each * seps + ST_length])[::-1])

    circuit = QuantumCircuit(index_count + seps * (M + M), index_count)

    ## Initialize
    for each in range(index_count):
        circuit.h(each)

    for each in range(len(pattern_string)):
        if pattern_string[each] == "1":
            circuit.x(index_count + seps * M + each)

    circuit.barrier()

    repeat = 1
    for ii in range(repeat):
        circuit = once_optimized(circuit, index_count, seps, M, pattern_string, ST)

    circuit.barrier()
    for each in range(index_count):
        circuit.measure(each, each)
    
    img = circuit_drawer(circuit, output='mpl', fold=1000000)
    buffered = io.BytesIO()
    img.savefig(buffered, format="PNG", bbox_inches='tight')
    plt.close('all')

    # 将字节流编码为 Base64 字符串
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    qasm_str = circuit.qasm()
    return img_str, qasm_str


def run_exp_fig(target_string, pattern_string, num):
    N = len(target_string)
    M = len(pattern_string)

    coding = None
    seps = 0

    if power_of_2(N):
        coding = {"A": "00", "C": "01", "G": "10", "T": "11"}
        seps = 2
    else:
        coding = {"A": "000", "C": "001", "G": "010", "T": "011", "$": "100"}
        seps = 3
        target_string = argumentation(target_string)
        N = len(target_string)

    target_string = encode(target_string, coding)
    pattern_string = encode(pattern_string, coding)

    index_count = 0
    while 2 ** index_count < N:
        index_count += 1

    ST_length = seps * M
    ST = []
    temp_target_string = target_string + target_string
    for each in range(2 ** index_count):
        ST.append(str(temp_target_string[each * seps: each * seps + ST_length])[::-1])

    circuit = QuantumCircuit(index_count + seps * (M + M), index_count)

    ## Initialize
    for each in range(index_count):
        circuit.h(each)

    for each in range(len(pattern_string)):
        if pattern_string[each] == "1":
            circuit.x(index_count + seps * M + each)

    circuit.barrier()

    repeat = int(num)
    for ii in range(repeat):
        circuit = once_optimized(circuit, index_count, seps, M, pattern_string, ST)

    circuit.barrier()
    for each in range(index_count):
        circuit.measure(each, each)
    
    # backend = Aer.get_backend('qasm_simulator')
    backend = QasmSimulator(method='matrix_product_state')
    job = execute(circuit, backend, shots=100)
    result = job.result()
    counts = result.get_counts(circuit)
    img = plot_histogram(counts)
    buffered = io.BytesIO()
    img.savefig(buffered, format="PNG", bbox_inches='tight')
    plt.close('all')

    # 将字节流编码为 Base64 字符串
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str