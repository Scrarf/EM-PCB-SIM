
import pybis
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import interp1d
from scipy.ndimage import shift
from scipy import signal
import random
import math
import skrf as rf


def generate_waveform_components(model_name='DQ40_ODT40'):
    output = pybis.IBSParser().parse('DDR3L.ibs')
    
    print("Available models:")
    for name, model in output.model.items():
        print(f"  - {name} ({model.model_type})")
    
    model = output.model[model_name]
    
    #for idx, wf in enumerate(model["Rising Waveform"]):
    #    print(f"Rising [{idx}]: V_fixture={wf.v_fixture}V, R_fixture={wf.r_fixture}Ω")
    
    waveform_rise_gnd = model["Rising Waveform"][0]
    waveform_rise_vcc = model["Rising Waveform"][1]
    
    rise_time_gnd, rise_voltage_gnd = waveform_rise_gnd.waveform.typ
    rise_time_vcc, rise_voltage_vcc = waveform_rise_vcc.waveform.typ
    
    rise_interpolated_gnd = interp1d(rise_time_gnd, rise_voltage_gnd, kind='cubic')(np.arange(0, (1e-9), dt))#[0:3000]
    rise_interpolated_vcc = interp1d(rise_time_vcc, rise_voltage_vcc, kind='cubic')(np.arange(0, (1e-9), dt))#[0:3000]
    rise_interpolated = (rise_interpolated_vcc + rise_interpolated_gnd) / 2
    
    waveform_fall_gnd = model["Falling Waveform"][0]
    waveform_fall_vcc = model["Falling Waveform"][1]
    
    fall_time_gnd, fall_voltage_gnd = waveform_fall_gnd.waveform.typ
    fall_time_vcc, fall_voltage_vcc = waveform_fall_vcc.waveform.typ
    
    fall_interpolated_gnd = interp1d(fall_time_gnd, fall_voltage_gnd, kind='cubic')(np.arange(0, (1e-9), dt))#[0:3000]
    fall_interpolated_vcc = interp1d(fall_time_vcc, fall_voltage_vcc, kind='cubic')(np.arange(0, (1e-9), dt))#[0:3000]
    fall_interpolated = (fall_interpolated_vcc + fall_interpolated_gnd) / 2

    return rise_interpolated, fall_interpolated



def generate_sequence(freq=500e6, size=10):
    period = 1 / freq #in seconds
    #extension = int(round((period / dt / 2) - len(rise_interpolated)))
    #hold = int(period / dt / 2)

    samples_per_period = int(round(period / dt))
    samples_per_half = samples_per_period // 2  # Integer divide to ensure 2 halves = 1 period
    extension = samples_per_half - len(rise_interpolated)
    hold = samples_per_half
    
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

def convolution(waveform_time, network, i, j):

    Nfft = 2 * len(waveform_time)
    waveform_fft = np.fft.fft(waveform_time, Nfft)
    f = np.fft.fftfreq(Nfft, dt)

    H = np.zeros(Nfft, dtype=complex)
    
    interp = interp1d(np.concatenate(([0], network.f)),
             np.concatenate(([np.real(network.s[0, i, j])], network.s[:, i, j])),
             fill_value=(None, 0),
             kind='linear',
             bounds_error=False)

    
    H[f >= 0] = interp(f[f >= 0])
    H[f < 0] = np.conj(interp(-f[f < 0]))
    

    filtered_fft = waveform_fft * H
    
    return np.real(np.fft.ifft(filtered_fft)[:len(waveform_time)])
    #return np.fft.ifft(filtered_fft)


dt = 1e-12 /3 # 1ps time step
freq = 300e6
size = 500

rise_interpolated, fall_interpolated = generate_waveform_components(model_name='DQ40_ODT40')

#real sequence
waveform_long = generate_sequence(freq=freq, size=size)
waveform_fft = np.fft.fft(waveform_long)

#perfect sequence
waveform_perfect = (signal.square(np.pi * np.linspace(np.pi/2, len(waveform_long) * dt * freq * 2 + np.pi/2, len(waveform_long))) + 1) / 2
waveform_fft_perfect = np.fft.fft(waveform_perfect)

#s parameter complex numbers. but X axis is not Hz its just points.
network = rf.Network('./touchstone/simulation.s2p')


#plt.style.use('dark_background')

f = np.fft.fftfreq(len(waveform_long), dt)
#t = np.arange(0, len(waveform_long) * dt, dt)
t = np.arange(len(waveform_long)) * dt

plt.figure() #new figure


plt.plot(t, waveform_perfect, label="waveform_perfect", alpha=0.3, color='red')
plt.plot(t, waveform_long, label="waveform", color='red')

plt.plot(t, convolution(waveform_time=waveform_long, network=network, i=1, j=0), label="convolution") 

plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.title('Time domain random bit sequence')
plt.grid(True)
plt.legend()


plt.figure() #new figure

plt.plot(f[f >= 0], (abs(waveform_fft_perfect) / len(waveform_fft_perfect))[f >= 0], label="fft_perfect", alpha=0.3, color='red')

plt.plot(f[f >= 0], (abs(waveform_fft) / len(waveform_fft))[f >= 0], label="fft", color='red')
#plt.plot(network.f, np.abs(network.s[:, 1, 0]), label="s21_abs", color="blue")


plt.title('Frequency domain random bit sequence')
plt.xlim(0, 5e9)
plt.grid()
plt.legend()


plt.figure() #new figure
plt.plot(network.f, abs(network.s[:, 1, 0]), label="s21_raw", color="blue")
plt.title('S-parameter real part')
plt.grid()
plt.legend()

plt.figure()

plt.scatter(t%(1/freq), convolution(waveform_time=waveform_long, network=network, i=1, j=0),
             c=range(len(t)),
             cmap='hsv',
             s=0.1,
             alpha=0.5)

plt.grid(True, linestyle='--', alpha=0.7)
plt.legend()
plt.title('Eye diagram')
 

plt.show()


