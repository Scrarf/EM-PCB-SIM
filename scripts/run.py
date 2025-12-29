import os
from CSXCAD import ContinuousStructure
import openEMS
import math
from openEMS.physical_constants import C0

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

csx = ContinuousStructure()



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


fdtd = openEMS.openEMS()
fdtd.SetCSX(csx)

print(f"STL bounds: {stl_reader.GetBoundBox()}")

expand = 5

mesh.AddLine('x', [86.5252 *mm - expand *mm, 106.401 *mm + expand *mm])
mesh.AddLine('y', [-75.918 *mm + expand *mm, -88.0904 *mm - expand *mm])
mesh.AddLine('z', [-2 *mm, 3 *mm])

mesh.AddLine('z', [0.4316 *mm, 0.4468 *mm, 0.5996 *mm, 0.6148 *mm]) # mesh lines for highres

mesh.SmoothMeshLines('x', res)
mesh.SmoothMeshLines('y', res)
mesh.SmoothMeshLines('z', res)

#mesh.AddEdge2Grid('x', res_fine) #check this next time
#mesh.AddEdge2Grid('y', res_fine)

#dump = csx.AddDump("field_dump", dump_type=0, file_type=1)
#dump.AddBox(start=[86.5252 *mm, -75.918 *mm, 0 *mm],
#            stop=[106.401 *mm, -88.0904 *mm, 1 *mm])


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

# view geometry
csx.Write2XML('geometry.xml')
os.system('AppCSXCAD geometry.xml')



fdtd.SetGaussExcite(f_max / 2, f_max / 2)
fdtd.SetBoundaryCond(["PML_12", "PML_12", "PML_12", "PML_12", "PML_12", "PML_12"])

sim_path = os.path.join(os.getcwd(), 'sim')
os.makedirs(sim_path, exist_ok=True)

fdtd.Run(sim_path)
