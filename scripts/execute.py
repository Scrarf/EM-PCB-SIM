import os
from CSXCAD import ContinuousStructure
import openEMS
import math
from openEMS.physical_constants import C0
import sys
engine_unit = 1 #openEMS still works in meeters
mm = 1e-3 #milimeter for muliplication

f_min = 100e6  # post-processing only, not used in simulation
f_max = 10e9   # determines mesh size and excitation signal bandwidth
epsilon_r = 1
v = C0 / math.sqrt(epsilon_r)
wavelength = v / f_max 
res = wavelength / 3e2
# use a smaller cell size around metal edge, not just the base mesh size
highres = res / 1.5

z0 = 50 #port impedence

expand = 5

sim_path = os.path.join(os.getcwd(), 'sim')

def generate_structure(csx, fdtd):
    material = csx.AddMetal('copper')
    stl_filename = '../stl/Traces_reduced.stl'
    stl_reader = material.AddPolyhedronReader(stl_filename)
    stl_reader.ReadFile()
    
    
    substrate = csx.AddMaterial('FR4')
    substrate.SetMaterialProperty(epsilon=4.2, kappa=0.02)  # FR4 properties
    
    # Create substrate box (adjust to your PCB dimensions)
    substrate_box = substrate.AddBox(
        start=[86.5252 *mm, -88.0904 *mm, 0.2 *mm],
        stop=[106.401 *mm, -75.918 *mm, 0.8 *mm]  # PCB thickness
    )
    
    mesh = csx.GetGrid()
    mesh.SetDeltaUnit(engine_unit)
    

    mesh.AddLine('x', [86.5252 *mm - expand *mm, 106.401 *mm + expand *mm])
    mesh.AddLine('y', [-75.918 *mm + expand *mm, -88.0904 *mm - expand *mm])
    mesh.AddLine('z', [-2 *mm, 3 *mm])
    
    mesh.AddLine('z', [0.4316 *mm, 0.4468 *mm, 0.5996 *mm, 0.6148 *mm]) # mesh lines for highres
    
    mesh.SmoothMeshLines('x', res)
    mesh.SmoothMeshLines('y', res)
    mesh.SmoothMeshLines('z', res)

    print(f"STL bounds: {stl_reader.GetBoundBox()}")

    port = [None, None, None, None]
    
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

    
    fdtd.SetGaussExcite(f_max / 2, f_max / 2)
    fdtd.SetBoundaryCond(["PML_12", "PML_12", "PML_12", "PML_12", "PML_12", "PML_12"])
    


    csx.Write2XML('geometry.xml')
    os.system('AppCSXCAD geometry.xml')
            

def simulate(csx, fdtd):
    
    fdtd.SetGaussExcite(f_max / 2, f_max / 2)
    fdtd.SetBoundaryCond(["PML_12", "PML_12", "PML_12", "PML_12", "PML_12", "PML_12"])

    fdtd.Run(sim_path)

    print("COMPLETE YAY!")

if __name__ == "__main__":
    csx = ContinuousStructure()
    fdtd = openEMS.openEMS()
    fdtd.SetCSX(csx)
    
    if len(sys.argv) <= 1:
        print('No command given, expect "generate", "simulate", "postproc"')
    elif sys.argv[1] in ["generate", "simulate"]:
        generate_structure(csx, fdtd)

        if sys.argv[1] == "simulate":
            # run simulator
            simulate(csx, fdtd)
    elif sys.argv[1] == "postproc":
        # run post-processing only, without running the simulator
        port = setup_ports(fdtd, csx)
        postproc(port)
    else:
        print("Unknown command %s" % sys.argv[1])
        exit(1)


