import h5py
import numpy as np
import matplotlib.pyplot as plt
import os
from matplotlib.colors import LogNorm
from matplotlib.colors import PowerNorm

port_number = 3

h5file = f"sim/port_{port_number}/field_dump.h5"
outdir = f"sim/port_{port_number}/png_frames/"
z_index = 0
cmap = "inferno"
dpi = 150

os.makedirs(outdir, exist_ok=True)

with h5py.File(h5file, "r") as f:
    td = f["FieldData/TD"]
    timesteps = sorted(td.keys())

    for i, t in enumerate(timesteps):
        data = td[t][:] # shape (3, Nz, Nx, Ny)

        Fx = data[0]
        Fy = data[1]
        Fz = data[2]
        
        mag = np.sqrt(Fx**2 + Fy**2 + Fz**2)
        
        img = mag[z_index, :, :]
        
        plt.figure(figsize=(6, 5))
        plt.imshow(img, origin="lower", cmap=cmap, norm=PowerNorm(gamma=0.5, vmin=0, vmax=4))
        
        plt.colorbar(label="|F|")
        plt.title(f"t = {t}")
        plt.xlabel("X")
        plt.ylabel("Y")
        
        fname = os.path.join(outdir, f"frame_{i:05d}.png")
        plt.savefig(fname, dpi=dpi)
        plt.close()

        print(f"Saved: {fname}")
