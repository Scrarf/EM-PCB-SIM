import os
from CSXCAD import ContinuousStructure
import openEMS
import math
from openEMS.physical_constants import C0
import sys
import numpy as np
import matplotlib.pylab as plt
import skrf
from ports import port_pos

engine_unit = 1 #openEMS still works in meeters
mm = 1e-3 #milimeter for muliplication

f_min = 1#100e6  # post-processing only, not used in simulation
f_max = 10e9   # determines mesh size and excitation signal bandwidth
epsilon_r = 1
resolution = 0.08 *mm
z0 = 50 #port impedence

expand = 1

port = [None] * len(port_pos)

sim_path = os.path.join(os.getcwd(), 'sim')

bounds = {}

#generated from blender
mesh_lines_z = [
    0.00043464, 0.00044395, 0.00060237, 0.00061161, 0.00091803, 0.00092672, 0.00108627, 0.00109467,
    0.00140124, 0.00140994
]

def generate_ports(csx, fdtd):

    #'exc' is a list of excited ports. firt port is index 1, follows name not array index.
    exc = {1}

    for i in port_pos:
        port[i] = fdtd.AddLumpedPort(i+1, z0,
                    port_pos[i][0],
                    port_pos[i][1],
                    'z', excite=1 if i+1 in exc else 0)
                                                                        
def generate_structure(csx, fdtd):
    
    substrate_material = csx.AddMaterial('FR4')
    substrate_material.SetMaterialProperty(epsilon=4.2, kappa=0.02)
    copper_material = csx.AddMetal('copper')
    
    substrate = substrate_material.AddPolyhedronReader('../stl/Substrate.stl')
    copper_traces = copper_material.AddPolyhedronReader('../stl/Traces.stl')
    copper_vias = copper_material.AddPolyhedronReader('../stl/Vias.stl')
    copper_pads = copper_material.AddPolyhedronReader('../stl/Pads.stl')

    
    substrate.SetPriority(1)
    copper_traces.SetPriority(2)
    copper_vias.SetPriority(3)
    copper_pads.SetPriority(4)
    
    substrate_debug = substrate.ReadFile()    
    copper_traces_debug = copper_traces.ReadFile()
    copper_vias_debug = copper_vias.ReadFile()
    copper_pads_debug = copper_pads.ReadFile()

    print(f"Substrate loaded: {substrate_debug}")
    print(f"Copper traces loaded: {copper_traces_debug}")
    print(f"Copper vias loaded: {copper_vias_debug}")
    print(f"Copper pads loaded: {copper_pads_debug}")

    print(f"substrate bounding box: {substrate.GetBoundBox()}")
    global bounds
    bounds = substrate.GetBoundBox()
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(engine_unit)


    mesh.AddLine('x', [bounds[0][0] - expand *mm, bounds[1][0] + expand *mm])
    mesh.AddLine('y', [bounds[0][1] - expand *mm, bounds[1][1] + expand *mm])
    mesh.AddLine('z', [bounds[0][2] - expand *mm, bounds[1][2] + expand *mm])

    #mesh.AddLine('z', [0.4316 *mm, 0.4468 *mm, 0.5996 *mm, 0.6148 *mm]) # mesh lines for highres
    #mesh.AddLine('z', [1.0828 *mm, 1.098 *mm, 1.398 *mm, 1.4132 *mm])

    #mesh lines for ports

    #lines_per_port = 5
    #port_count = len(port_pos)
    #for i in range(lines_per_port + 1):
    #    for j in port_pos:
    #        mesh.AddLine('x', [port_pos[j][0][0] + (port_pos[j][1][0] - port_pos[j][0][0]) * i/lines_per_port])

    #mesh.AddLine('x', mesh_lines_x)
    #mesh.AddLine('y', mesh_lines_y)
    mesh.AddLine('z', mesh_lines_z)

    mesh.SmoothMeshLines('x', resolution)
    mesh.SmoothMeshLines('y', resolution)
    mesh.SmoothMeshLines('z', resolution)
            
def open_view(csx, fdtd):    
    csx.Write2XML('geometry.xml')
    os.system('AppCSXCAD geometry.xml')
    

def simulate(csx, fdtd):
    fdtd.SetEndCriteria(1e-5)
    #fdtd.SetOverSampling(4)
    
    fdtd.SetGaussExcite(f_max / 2, f_max / 2)
    fdtd.SetBoundaryCond(["PML_12", "PML_12", "PML_12", "PML_12", "PML_12", "PML_12"])

    dump = csx.AddDump("field_dump", dump_type=0, file_type=1)
    dump.AddBox(start=[bounds[0][0], bounds[0][1], bounds[0][2]],
                stop=[bounds[1][0], bounds[1][1], bounds[1][2]])
    
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

    s_matrix = np.zeros((points, 2, 2), dtype=complex)
    s_matrix[:, 0, 0] = port[0].uf_ref / port[0].uf_inc
    s_matrix[:, 1, 0] = port[1].uf_ref / port[0].uf_inc
    s_matrix[:, 0, 1] = port[1].uf_ref / port[0].uf_inc
    s_matrix[:, 1, 1] = port[0].uf_ref / port[0].uf_inc

    freq = skrf.Frequency.from_f(freq_list, unit='hz')

    network = skrf.Network(
        frequency=freq,
        s=s_matrix,
        z0=z0
    )
    
    if arg == 's_param':
        print("Plotting S-parameters...")

        s11_db_list = 10 * np.log10(np.abs(s_matrix[:, 0, 0]) ** 2)
        s21_db_list = 10 * np.log10(np.abs(s_matrix[:, 1, 0]) ** 2) 
            
        plt.plot(freq_list / 1e9, s11_db_list, label='$S_{11}$ dB')
        plt.plot(freq_list / 1e9, s21_db_list, label='$S_{21}$ dB')

        #plt.xscale('log')
        plt.title("S-parameters")    
        plt.grid(which='both')
        plt.legend()
        plt.xlabel("GHz")
        plt.ylabel("dB")
        
    if arg == 'smith_chart':

        skrf.stylely()
        plt.figure()
        network.plot_s_smith(m=0, n=0)   # S11 Smith chart
        plt.title("S11 Smith Chart")

    if arg == 'tdr':
        
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
        
    if arg == 'save_touchstone':                        
            network.write_touchstone('./touchstone/simulation.s2p')
            print("Touchstone file saved as simulation.s2p")


    plt.show()

    
if __name__ == "__main__":
    csx = ContinuousStructure()
    fdtd = openEMS.openEMS()
    fdtd.SetCSX(csx)
    
    if len(sys.argv) <= 1:
        print('No command given, expect "generate", "simulate", "postproc", "debug"')
    elif sys.argv[1] == "generate":
        generate_structure(csx, fdtd)
        generate_ports(csx, fdtd)
        open_view(csx, fdtd)
    elif sys.argv[1] == "simulate":
        generate_structure(csx, fdtd)
        generate_ports(csx, fdtd)
        open_view(csx, fdtd)
        simulate(csx, fdtd)
    elif sys.argv[1] == "debug":
        generate_structure(csx, fdtd)
        generate_ports(csx, fdtd)
        debug(csx, fdtd)
            
    elif sys.argv[1] == "postproc":
        if len(sys.argv) <= 2 or sys.argv[2] not in ["s_param", "smith_chart", "tdr", "save_touchstone"]:
            print('postproc requires 2 arguments, expect "s_param", "smith_chart", "tdr", "save_touchstone"')
        else:
            generate_structure(csx, fdtd)
            generate_ports(csx, fdtd)
            postproc(sys.argv[2])
    else:
        print("Unknown command %s" % sys.argv[1])
        exit(1)


