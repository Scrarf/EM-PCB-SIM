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
resolution = 0.04 *mm
z0 = 50 #port impedence

expand = 0.5

port = [None] * 2
sim_path = os.path.join(os.getcwd(), 'sim')

#port_pos = [[[None] * 2] * 3] * 2
port_pos = np.zeros([2, 2, 3])

port_pos[0] = [[0.137106, -0.114705, 0.000930],
              [0.137253, -0.114557, 0.001083]]
port_pos[1] = [[0.132482, -0.110080, 0.000930],
              [0.132629, -0.109932, 0.001083]]
              
#bounds start.x start.y end.x end.y end.z
bounds = [129.75 *mm, -117.388 *mm, 0 *mm, 140.05 *mm, -107.338 *mm, 1.5296 *mm]

#generated from blender
mesh_lines_z = [
    0.00091713, 0.00092794, 0.00092221, 0.00043938, 0.00044416, 0.00043461, 0.00109013, 0.00108543,
    0.00109554, 0.00140549, 0.00141045, 0.00140101
]
def generate_ports(csx, fdtd):
    
    #pec = csx.AddMetal('pec')
    
    #port[0] = fdtd.AddMSLPort(1, pec,
    #                port_pos[0][0],
    #                port_pos[0][1],
    #                'x', 'z', excite=-1, priority=100)

    port[0] = fdtd.AddLumpedPort(1, z0,
                    port_pos[0][0],
                    port_pos[0][1],
                    'z', excite=1)
    port[1] = fdtd.AddLumpedPort(2, z0,
                    port_pos[1][0],
                    port_pos[1][1],
                    'z', excite=0)

                                                                        
def generate_structure(csx, fdtd):
    
    substrate_material = csx.AddMaterial('FR4')
    substrate_material.SetMaterialProperty(epsilon=4.2, kappa=0.02)
    copper_material = csx.AddMetal('copper')
    
    substrate = substrate_material.AddPolyhedronReader('../stl/Substrate.001.stl')
    copper_traces = copper_material.AddPolyhedronReader('../stl/Traces.001.stl')
    copper_vias = copper_material.AddPolyhedronReader('../stl/Vias.001.stl')

    
    substrate.SetPriority(1)
    copper_traces.SetPriority(2)
    copper_vias.SetPriority(3)
    
    substrate_debug = substrate.ReadFile()    
    copper_traces_debug = copper_traces.ReadFile()
    copper_vias_debug = copper_vias.ReadFile()

    print(f"Substrate loading success: {substrate_debug}")
    print(f"Copper traces loading success: {copper_traces_debug}")
    print(f"Copper vias loading success: {copper_vias_debug}")
    
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(engine_unit)


    mesh.AddLine('x', [bounds[0] - expand *mm, bounds[3] + expand *mm])
    mesh.AddLine('y', [bounds[1] - expand *mm, bounds[4] + expand *mm])
    mesh.AddLine('z', [bounds[2] - expand *mm, bounds[5] + expand *mm])

    #mesh.AddLine('z', [0.4316 *mm, 0.4468 *mm, 0.5996 *mm, 0.6148 *mm]) # mesh lines for highres
    #mesh.AddLine('z', [1.0828 *mm, 1.098 *mm, 1.398 *mm, 1.4132 *mm])

    #mesh lines for ports

    lines_per_port = 5
    port_count = 2
    for i in range(lines_per_port + 1):
        for j in range(port_count):
            mesh.AddLine('x', [port_pos[j][0][0] + (port_pos[j][1][0] - port_pos[j][0][0]) * i/lines_per_port])
            mesh.AddLine('y', [port_pos[j][0][1] + (port_pos[j][1][1] - port_pos[j][0][1]) * i/lines_per_port])

    #for i in range(6):
    #    mesh.AddLine('z', [port_pos[0][0][2] + (port_pos[0][1][2] - port_pos[0][0][2]) * i/5])

    

    #mesh.AddLine('x', mesh_lines_x)
    #mesh.AddLine('y', mesh_lines_y)
    mesh.AddLine('z', mesh_lines_z)

    mesh.SmoothMeshLines('x', resolution)
    mesh.SmoothMeshLines('y', resolution)
    mesh.SmoothMeshLines('z', resolution)

    #print(stl_reader.GetBoundBox())
            
def open_view(csx, fdtd):    
    csx.Write2XML('geometry.xml')
    os.system('AppCSXCAD geometry.xml')
    

def simulate(csx, fdtd):
    fdtd.SetEndCriteria(1e-5)
    #fdtd.SetOverSampling(4)
    
    fdtd.SetGaussExcite(f_max / 2, f_max / 2)
    fdtd.SetBoundaryCond(["PML_12", "PML_12", "PML_12", "PML_12", "PML_12", "PML_12"])
    
    #dump = csx.AddDump("field_dump", dump_type=0, file_type=1)
    #dump.AddBox(start=[bounds[0], bounds[1], bounds[2]],
    #            stop=[bounds[3], bounds[4], bounds[5]])
    
    fdtd.Run(sim_path)
    
    print("COMPLETE YAY!")

def debug(csx, fdtd):
    fdtd.SetGaussExcite(f_max / 2, f_max / 2)
    fdtd.Run(sim_path, debug_pec=True, verbose=3, setup_only=1, debug_material=True, debug_operator=True)
    print("debug complete")
    

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
            
        plt.plot(freq_list, s11_db_list, label='$S_{11}$ dB')
        plt.plot(freq_list, s21_db_list, label='$S_{21}$ dB')

        plt.xscale('log')
        plt.title("S-parameters")    
        plt.grid(which='both')
        plt.legend()
        plt.xlabel("Hz")
        plt.ylabel("dB")
        
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
        print('No command given, expect "generate", "simulate", "postproc", "debug"')
    elif sys.argv[1] in ["generate", "simulate", "debug"]:
        generate_structure(csx, fdtd)
        generate_ports(csx, fdtd)
        open_view(csx, fdtd)
        
        if sys.argv[1] == "simulate":
            # run simulator
            simulate(csx, fdtd)
        elif sys.argv[1] == "debug":
            debug(csx, fdtd)
            
    elif sys.argv[1] == "postproc":
        if len(sys.argv) <= 2:
            print('postproc requires 2 arguments, expect "s_param", "smith_chart", "tdf"')
        else:
            generate_structure(csx, fdtd)
            generate_ports(csx, fdtd)
            postproc(sys.argv[2])
    else:
        print("Unknown command %s" % sys.argv[1])
        exit(1)


