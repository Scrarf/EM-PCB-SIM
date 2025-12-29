import numpy as np
import matplotlib.pylab as plt
import openEMS
import os

f_min = 100e6  # post-processing only, not used in simulation
f_max = 10e9   # determines mesh size and excitation signal bandwidth

z0 = 50

# Load data
#time, V1 = np.loadtxt('sim/port_ut_1', unpack=True, comments='%')
#_,    I1 = np.loadtxt('sim/port_it_1', unpack=True, comments='%')
#_,    V2 = np.loadtxt('sim/port_ut_2', unpack=True, comments='%')
#_,    I2 = np.loadtxt('sim/port_it_2', unpack=True, comments='%')

# FFT
#V1_fft = np.fft.rfft(V1)
#I1_fft = np.fft.rfft(I1)
#V2_fft = np.fft.rfft(V2)
#I2_fft = np.fft.rfft(I2)

# Waves

#V1_inc = (V1_fft + z0*I1_fft) / 2
#V1_ref = (V1_fft - z0*I1_fft) / 2
#V2_ref = (V2_fft - z0*I2_fft) / 2

# S-parameters
#S11 = V1_ref / V1_inc
#S21 = V2_ref / V1_inc

# Frequency axis
#freq = np.fft.rfftfreq(len(time), time[1]-time[0])

#print(time[1])

sim_path = os.path.join(os.getcwd(), 'sim')

fdtd = openEMS.openEMS()

port = [None, None, None, None]  #np.shape(4)


port[0] = fdtd.AddLumpedPort(1, z0,
                [0.102895, -0.077755, 0.000443],
                [0.103505, -0.077145, 0.000607],
                'z', excite=1)
port[1] = fdtd.AddLumpedPort(2, z0,
                [0.102895, -0.079355, 0.000443],
                [0.103505, -0.078745, 0.000607],
                'z', excite=0)
port[2] = fdtd.AddLumpedPort(3, z0,
                [0.090695, -0.084405, 0.000443],
                [0.091305, -0.083795, 0.000607],
                'z', excite=0)
port[3] = fdtd.AddLumpedPort(4, z0,
                [0.088295, -0.084405, 0.000443],
                [0.088905, -0.083795, 0.000607],
                'z', excite=0)


points = 1000

freq_list = np.linspace(f_min, f_max, points)


#for p in port:
#    p.CalcPort(sim_path, freq_list, ref_impedance=z0)
#    print(p)

port[0].CalcPort(sim_path, freq_list, ref_impedence=z0)

print(sim_path)
#s11_list = port[0].uf_ref / port[0].uf_inc

#print(port[0])
