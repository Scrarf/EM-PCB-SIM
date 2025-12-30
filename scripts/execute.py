import os
from CSXCAD import ContinuousStructure
import openEMS
import math
from openEMS.physical_constants import C0
import sys
import numpy as np
import matplotlib.pylab as plt
import skrf

engine_unit = 1 #openEMS still works in meeters
mm = 1e-3 #milimeter for muliplication

f_min = 100e6  # post-processing only, not used in simulation
f_max = 10e9   # determines mesh size and excitation signal bandwidth
epsilon_r = 1
v = C0 / math.sqrt(epsilon_r)
wavelength = v / f_max 
res = wavelength / 3e2

z0 = 50 #port impedence

expand = 3

port = [None] * 4
sim_path = os.path.join(os.getcwd(), 'sim')

def generate_ports():
    
    port[0] = fdtd.AddLumpedPort(1, z0,
                    [0.102895, -0.077755, 0.000443],
                    [0.103640, -0.076997, 0.000607],
                    'z', excite=1)
    port[1] = fdtd.AddLumpedPort(2, z0,
                    [0.102895, -0.079355, 0.000443],
                    [0.103505, -0.078745, 0.000607],
                    'z', excite=0)
    port[2] = fdtd.AddLumpedPort(3, z0,
                    [0.090538, -0.084405, 0.000443],
                    [0.091305, -0.083576, 0.000607],
                    'z', excite=0)
    port[3] = fdtd.AddLumpedPort(4, z0,
                    [0.088295, -0.084405, 0.000443],
                    [0.088905, -0.083795, 0.000607],
                    'z', excite=0)
                    

def generate_structure(csx, fdtd):
    material = csx.AddMetal('copper')
    
    stl_reader = material.AddPolyhedronReader('../stl/Traces.001.stl')
    stl_reader = material.AddPolyhedronReader('../stl/Vias.001.stl')
    #stl_reader = material.AddPolyhedronReader('../stl/Pads.001.stl')
    stl_reader.ReadFile()

    
    substrate = csx.AddMaterial('FR4')
    substrate.SetMaterialProperty(epsilon=4.2, kappa=0.02)  # FR4 properties

    substrate_box = substrate.AddPolyhedronReader('../stl/Substrate.001.stl')
    # Create substrate box (adjust to your PCB dimensions)
    #substrate_box = substrate.AddBox(
    #    start=[86.5252 *mm, -88.0904 *mm, 0.2 *mm],
    #    stop=[106.401 *mm, -75.918 *mm, 0.8 *mm]  # PCB thickness
    #)
    
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(engine_unit)
    

    mesh.AddLine('x', [81.7372 *mm - expand *mm, 107.702 *mm + expand *mm])
    mesh.AddLine('y', [-62.1323 *mm + expand *mm, -89.1735 *mm - expand *mm])
    mesh.AddLine('z', [-2 *mm, 3 *mm])
    
    mesh.AddLine('z', [0.4316 *mm, 0.4468 *mm, 0.5996 *mm, 0.6148 *mm]) # mesh lines for highres
    
    mesh.SmoothMeshLines('x', res)
    mesh.SmoothMeshLines('y', res)
    mesh.SmoothMeshLines('z', res)

    print(f"STL bounds: {stl_reader.GetBoundBox()}")
    
    csx.Write2XML('geometry.xml')
    os.system('AppCSXCAD geometry.xml')
            

def simulate(csx, fdtd):
    fdtd.SetEndCriteria(1e-5)
        
    fdtd.SetGaussExcite(f_max / 2, f_max / 2)
    fdtd.SetBoundaryCond(["PML_12", "PML_12", "PML_12", "PML_12", "PML_12", "PML_12"])

    dump = csx.AddDump("field_dump", dump_type=0, file_type=1)
    dump.AddBox(start=[81.7372 *mm, -62.1323 *mm, 0 *mm],
                stop=[107.702 *mm, -89.1735 *mm, 1.5296 *mm])
    
    fdtd.Run(sim_path)
    
    print("COMPLETE YAY!")

def postproc(arg):
    
    points = 1000
    
    freq_list = np.linspace(f_min, f_max, points)
    
    port[0].CalcPort(sim_path, freq_list, z0)
    port[1].CalcPort(sim_path, freq_list, z0)


    s11_list = port[0].uf_ref / port[0].uf_inc
    s21_list = port[1].uf_ref / port[0].uf_inc

    s12_list = s21_list
    s22_list = s11_list

    
    if arg == 's_param':
        print("Plotting S-parameters...")

        s11_db_list = 10 * np.log10(np.abs(s11_list) ** 2)
        s21_db_list = 10 * np.log10(np.abs(s21_list) ** 2) 
            
        plt.plot(freq_list / 1e9, s11_db_list, label='$S_{11}$ dB')
        plt.plot(freq_list / 1e9, s21_db_list, label='$S_{21}$ dB')

        plt.title("S-parameters")    
        plt.grid()
        plt.legend()
        
    if arg == 'smith_chart':

        s_matrix = np.zeros((points, 2, 2), dtype=complex)
                
        s_matrix[:, 0, 0] = s11_list
        s_matrix[:, 1, 0] = s21_list
        s_matrix[:, 0, 1] = s12_list
        s_matrix[:, 1, 1] = s22_list

        freq = skrf.Frequency.from_f(freq_list, unit='hz')

        network = skrf.Network(
            frequency=freq,
            s=s_matrix,
            z0=50
        )

        skrf.stylely()
        plt.figure()
        network.plot_s_smith(m=0, n=0)   # S11 Smith chart
        plt.title("S11 Smith Chart")

    if arg == 'tdr':

        s_matrix = np.zeros((points, 2, 2), dtype=complex)
                
        s_matrix[:, 0, 0] = s11_list
        s_matrix[:, 1, 0] = s21_list
        s_matrix[:, 0, 1] = s12_list
        s_matrix[:, 1, 1] = s22_list

        freq = skrf.Frequency.from_f(freq_list, unit='hz')

        network = skrf.Network(
            frequency=freq,
            s=s_matrix,
            z0=50
        )

            
        network_dc = network.extrapolate_to_dc(kind='linear')
        
        plt.figure()
        plt.title("Time Domain Reflectometry - Step")
        network_dc.s11.plot_z_time_step(window='hamming', label="impedance")
        plt.xlim([-1, 2])  # look at the first two nanoseconds
        plt.show()
        
        plt.figure()
        plt.title("Time Domain Reflectometry - Impulse")
        network_dc.s11.plot_z_time_impulse(window='hamming', label="impedance")
        plt.xlim([-1, 2])  # look at the first two nanoseconds
        plt.show()
    
    plt.show()

    
if __name__ == "__main__":
    csx = ContinuousStructure()
    fdtd = openEMS.openEMS()
    fdtd.SetCSX(csx)
    
    if len(sys.argv) <= 1:
        print('No command given, expect "generate", "simulate", "postproc"')
    elif sys.argv[1] in ["generate", "simulate"]:
        generate_ports()
        generate_structure(csx, fdtd)

        if sys.argv[1] == "simulate":
            # run simulator
            simulate(csx, fdtd)
    elif sys.argv[1] == "postproc":
        if len(sys.argv) <= 2:
            print('postproc requires 2 arguments, expect "s_param", "smith_chart", ""')
        else:
            generate_ports()
            postproc(sys.argv[2])
    else:
        print("Unknown command %s" % sys.argv[1])
        exit(1)


