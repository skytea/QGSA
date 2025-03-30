import numpy as np
from ezQpy import *
login_key = 'XXXXXXXXXXX'
machine_name ='ClosedBetaQC'
shots = 5000


class Qgate():
    def __init__(self):
        self.fixed_X_gate = '''X Q%s\n'''
        self.fixed_Z_gate = '''Z Q%s\n'''
        self.fixed_H_gate = '''H Q%s\n'''
        self.fixed_CZ_gate = '''CZ Q%s Q%s\n'''
        self.fixed_measure_gate = '''M Q%s\n'''
    def H_gate(self, bit):
        return self.fixed_H_gate % (bit)
    def Z_gate(self, bit):
        return self.fixed_Z_gate % (bit)

    def X_gate(self, bit):
        return self.fixed_X_gate % (bit)
    def CZ_gate(self, bit1, bit2):
        return self.fixed_CZ_gate % (bit1, bit2)
    def CX_gate(self, bit1, bit2):
        cir = ''''''
        cir += self.H_gate(bit2)
        cir += self.CZ_gate(bit1, bit2)
        cir += self.H_gate(bit2)
        return cir

    def measure_gate(self, bit):
        return self.fixed_measure_gate % (bit)


class string_Grover():
    def __init__(self):
        self.G = Qgate()

    def circuit(self):
        # q0=13
        # q1 = 19
        # q2 = 25
        # q3 = 8
        # q4 = 20
        # q5 = 14
        q0 = 9
        q1 = 14
        q2 = 21
        q3 = 3
        q4 = 15
        q5 = 10
        # q0 = 1
        # q1 = 2
        # q2 =3
        # q3 = 4
        # q4 = 5
        # q5 = 6
        cir = ""
        #init
        cir += self.G.H_gate(q0)
        cir += self.G.H_gate(q1)
        cir += self.G.X_gate(q4)
        # cir += self.G.X_gate(q5)
        #oracle
        #make solution
        cir += self.G.CX_gate(q0,q3)
        cir += self.G.CX_gate(q1, q2)
        cir += self.G.CX_gate(q2, q4)
        cir += self.G.CX_gate(q3, q5)
        #find solution
        cir += self.G.X_gate(q4)
        cir += self.G.X_gate(q5)
        cir += self.G.CZ_gate(q4,q5)
        cir += self.G.X_gate(q4)
        cir += self.G.X_gate(q5)
        #uncomputation
        cir += self.G.CX_gate(q3, q5)
        cir += self.G.CX_gate(q2, q4)
        cir += self.G.CX_gate(q1, q2)
        cir += self.G.CX_gate(q0, q3)
        #amplication
        cir += self.G.H_gate(q0)
        cir += self.G.H_gate(q1)
        cir += self.G.Z_gate(q0)
        cir += self.G.Z_gate(q1)
        cir += self.G.CZ_gate(q0, q1)
        cir += self.G.H_gate(q0)
        cir += self.G.H_gate(q1)
        #measure
        cir += self.G.measure_gate(q0)
        cir += self.G.measure_gate(q1)
        return cir


    def solve(self):
        MAX_NUM=1
        num =1
        while(num<=MAX_NUM):
            print("W---->",num,"/",MAX_NUM)
            account = Account(login_key=login_key, machine_name=machine_name)
            cir = self.circuit()
            query_id = account.submit_job(circuit=cir,num_shots=shots)
            # outputstate = {}
            if query_id:
                outputstate = account.query_experiment(query_id, max_wait_time=360)
                value = outputstate
                f = open("XXXXXX"+str(num)+".txt", 'w')
                f.write(str(value))
                f.close()
                probability=outputstate["probability"]
                print(probability)
                num=num+1
            else:
                num=num+1
                print("error")


    def p_cir(self):
        cir=self.circuit()
        f = open("./Gate.txt", 'w')
        f.write(cir)
        f.close()
        print(cir)


SG = string_Grover()
SG.solve()
# SG.p_cir()