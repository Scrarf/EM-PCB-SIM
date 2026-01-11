
import pybis
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import shift
from scipy import signal
import random
import math


output = pybis.IBSParser().parse('DDR3L.ibs')

print("Available models:")
for name, model in output.model.items():
    print(f"  - {name} ({model.model_type})")

model = output.model['DQ40_ODT40']

#for idx, wf in enumerate(model["Rising Waveform"]):
#    print(f"Rising [{idx}]: V_fixture={wf.v_fixture}V, R_fixture={wf.r_fixture}Ω")

dt = 1e-12  # 1ps time step

waveform_rise_gnd = model["Rising Waveform"][0]
waveform_rise_vcc = model["Rising Waveform"][1]

rise_time_gnd, rise_voltage_gnd = waveform_rise_gnd.waveform.typ
rise_time_vcc, rise_voltage_vcc = waveform_rise_vcc.waveform.typ

rise_interpolated_gnd = interp1d(rise_time_gnd, rise_voltage_gnd, kind='cubic')(np.arange(0, (1e-9), dt))[0:1000]
rise_interpolated_vcc = interp1d(rise_time_vcc, rise_voltage_vcc, kind='cubic')(np.arange(0, (1e-9), dt))[0:1000]
rise_interpolated = (rise_interpolated_vcc + rise_interpolated_gnd) / 2

waveform_fall_gnd = model["Falling Waveform"][0]
waveform_fall_vcc = model["Falling Waveform"][1]

fall_time_gnd, fall_voltage_gnd = waveform_fall_gnd.waveform.typ
fall_time_vcc, fall_voltage_vcc = waveform_fall_vcc.waveform.typ

fall_interpolated_gnd = interp1d(fall_time_gnd, fall_voltage_gnd, kind='cubic')(np.arange(0, (1e-9), dt))[0:1000]
fall_interpolated_vcc = interp1d(fall_time_vcc, fall_voltage_vcc, kind='cubic')(np.arange(0, (1e-9), dt))[0:1000]
fall_interpolated = (fall_interpolated_vcc + fall_interpolated_gnd) / 2


def generate_sequence(freq=500e6, size=10):
    period = 1 / freq #in seconds
    extension = int((period / dt / 2) - len(rise_interpolated))
    hold = int(period / dt / 2)
    state = 0
    print(f'extension: {extension}')
    print(f'hold: {hold}')
    waveform = np.zeros(0)
    for i in range(size*2):
        #random.choice([True, False])
        if random.choice([True, False]):
            if state:
                waveform = np.concatenate([waveform, fall_interpolated, np.full(extension, fall_interpolated[-1])])
            else:
                waveform = np.concatenate([waveform, rise_interpolated, np.full(extension, rise_interpolated[-1])])
                
            state = ~state
        else:
            if state:
                waveform = np.concatenate([waveform, np.full(hold, rise_interpolated[-1])])
            else:
                waveform = np.concatenate([waveform, np.full(hold, fall_interpolated[-1])])
            
    return waveform

freq = 300e6
size = 50

waveform_long = generate_sequence(freq=freq, size=size)

waveform_fft = np.fft.fft(waveform_long)

waveform_perfect = (signal.square(np.pi * np.linspace(np.pi/2, len(waveform_long) * dt * freq * 2 + np.pi/2, len(waveform_long))) + 1) / 2
waveform_fft_perfect = np.fft.fft(waveform_perfect)


plt.plot(np.arange(0, len(waveform_perfect) * dt, dt), waveform_perfect, label="waveform_perfect", alpha=0.3, color='red')
plt.plot(np.arange(0, len(waveform_long) * dt, dt), waveform_long, label="waveform", color='red')


plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Rising Waveform - DQ40_ODT0')
plt.grid(True)
plt.legend()

plt.figure()

f_p = np.fft.fftfreq(len(waveform_perfect), dt)
plt.plot(f_p[f_p >= 0], (abs(waveform_fft_perfect) / len(waveform_fft_perfect))[f_p >= 0], label="fft_perfect", alpha=0.3, color='red')

f = np.fft.fftfreq(len(waveform_long), dt)
plt.plot(f[f >= 0], (abs(waveform_fft) / len(waveform_fft))[f >= 0], label="fft", color='red')


plt.xlim(0, 5e9)
plt.grid()
plt.legend()
#plt.xscale('log')
#plt.yscale('log')


plt.show()


     
        






