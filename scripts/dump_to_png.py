import h5py
import numpy as np
import matplotlib.pyplot as plt
import os

# -----------------------------
# User settings
# -----------------------------
h5file = "sim/field_dump.h5"
outdir = "png_frames"
z_index = 34          # <-- choose Z slice here
cmap = "inferno"
dpi = 150

os.makedirs(outdir, exist_ok=True)

# -----------------------------
# Load and process
# -----------------------------
with h5py.File(h5file, "r") as f:
    td = f["FieldData/TD"]
    timesteps = sorted(td.keys())

    for i, t in enumerate(timesteps):
        data = td[t][:]        # shape: (3, Nz, Nx, Ny)

        # Vector components
        Fx = data[0]
        Fy = data[1]
        Fz = data[2]

        # Magnitude
        mag = np.sqrt(Fx**2 + Fy**2 + Fz**2)

        # Z slice → X–Y image
        img = mag[z_index, :, :]

        # Plot
        plt.figure(figsize=(6, 5))
        plt.imshow(img, origin="lower", cmap=cmap)
        plt.colorbar(label="|F|")
        plt.title(f"t = {t}, z = {z_index}")
        plt.xlabel("X")
        plt.ylabel("Y")

        fname = os.path.join(outdir, f"frame_{i:05d}.png")
        plt.savefig(fname, dpi=dpi)
        plt.close()

        print(f"Saved {fname}")
