import math
import numpy as np
from qiskit import *
from qiskit.visualization import plot_histogram
import matplotlib.pyplot as plt
from qiskit.circuit.library import MCMT
from qiskit.visualization import circuit_drawer, plot_state_city
from qiskit.visualization import matplotlib as qiskit_matplotlib
from qiskit.providers.aer import QasmSimulator


def GetOneLength(i): # 获取二进制串中为1的数量
    binary_string = bin(i)
    IQS=binary_string[2:]
    return IQS.count('1')


def Container(i, k):
    binary_string_i = bin(i)
    IQSi = binary_string_i[2:]
    binary_string_k = bin(k)
    IQSk = binary_string_k[2:]
    max_length = max(len(IQSi), len(IQSk))
    IQSi_padded = IQSi.zfill(max_length)
    IQSk_padded = IQSk.zfill(max_length)
    # XOR(XOR(IQSi_padded,IQSk_padded),IQSi_padded) ，这个条件不太对，还是按照原本的说法
    for b1, b2 in zip(IQSi_padded, IQSk_padded):
        if b1 == '1' and b2 != '1':
            return False
    return True


def AppendPointer(N):# i和k都是从0开始的，j表示第j列,所以j需要-1
    pointer = {}
    for i in range(1, N):
        j=GetOneLength(i)
        for k in range(i+1, N):
            if Container(i, k):
                name = str(i) + "_" + str(j-1)
                if name not in pointer:
                    pointer[name] = [k]
                else:
                    pointer[name].append(k)
    return pointer


def FlipBit(char):
    if char == '0':
        return '1'
    return '0'


def GetOnePositions(s):
    s = s[::-1]
    positions = [index for index, char in enumerate(s) if char == '1']
    return positions


def GetIndexBit(pos):
    result = ''
    for item in pos:
        if result != '':
            result += ","
        result += "IB_" + str(item)
    return result


def GetIndexBit_(pos):
    result = []
    for item in pos:
        result.append(int(item))
    return result


def UpdateCT(index, CT, pointer, N):#这个函数不会出现j=0的情况
    binary_string = bin(index)
    IQS = binary_string[2:]
    j = IQS.count('1') - 1
    name = str(index)+"_"+str(j)
    if index >= N - 1:
        return CT
    if name in pointer:
        pos = pointer[name]
        for item in pos:
            CT[item][j] = CT[item][j] + 1
    else:
        raise ValueError("不存在指针:"+name+"!!!")
    return CT


def GetQC_k(TB_k, CT, ST, pointer, index_count, re):
    N = len(ST)
    TB_k0 = ST[0][::-1][TB_k]
    for index in range(N):
        binary_string = bin(index)
        IQS = binary_string[2:]
        TB_ki = ST[index][::-1][TB_k]
        if index == 0 and TB_k0 == "1":#添加X门
            # qc_name.append(["X", "TB_"+TB_k])
            re.append(('x', index_count + TB_k))
            # TB_k0 = FlipBit(TB_k0)
        else: # index!=0
            SUM = sum(CT[index])
            if SUM % 2 == 0:
                temp = TB_k0
            else:
                temp = FlipBit(TB_k0)
            if temp != TB_ki: # 添加量子门
                bit_1_length = GetOneLength(index)
                if bit_1_length == 1:
                    # indexPos = GetIndexBit(GetOnePositions(IQS))
                    # qc_name.append(["CX", indexPos, "TB_" + str(TB_k)])
                    indexPos = GetIndexBit_(GetOnePositions(IQS))
                    re.append(('cx', indexPos, index_count + TB_k))
                    CT = UpdateCT(index, CT, pointer, N)
                else: #bit_1_length>1
                    # indexPos = GetIndexBit(GetOnePositions(IQS))
                    # qc_name.append(["Toffoli", indexPos, "TB_"+str(TB_k)])
                    indexPos = GetIndexBit_(GetOnePositions(IQS))
                    re.append(('mcx', indexPos, index_count + TB_k))
                    CT = UpdateCT(index, CT, pointer, N)

    return re


def optimization(truth_table, index_count):
    TB_number = len(truth_table[0])
    N = len(truth_table)
    logN = int(math.log(N, 2))
    pointer = AppendPointer(len(truth_table))
    circuit = []
    for k in range(TB_number):
        # 创建计数表
        CT = [[0] * logN for _ in range(N)] #初始化计数表
        circuit = GetQC_k(k, CT, truth_table, pointer, index_count, circuit)

    return circuit

# # ST = ["00", "11", "10", "01"]  # 简化真值表
# ST = ["000", "110", "101", "001", "011", "010", "100", "001"]  # 简化真值表
# index_count = 3
# sep = 3
# M = 1
# print(optimization(ST, index_count))