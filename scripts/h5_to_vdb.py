import h5py
import openvdb as vdb


f = h5py.File("simulate-E_magnitude.h5", "r")
E = f["e_mag.r"]        # (Nt, Nx, Ny, Nz)


print(f"{E.shape}")

grid = vdb.FloatGrid()

print("Starting")

for i in range(E.shape[3]):
    grid.copyFromArray(E[:, :, :, i])
    grid.name = 'density'

    vdb.write(f"vdb/frame_{i}.vdb", grids=[grid])
    print(f"Frame: {i}")

print("Finished")

# Set density = 1 for the single point


