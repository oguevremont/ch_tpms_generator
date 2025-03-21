import trimesh
import numpy as np
import pyvista as pv
from scipy.ndimage import binary_fill_holes
from scipy.ndimage import distance_transform_edt
import porespy as ps
from skimage.measure import label, marching_cubes, block_reduce
import matplotlib.pyplot as plt
import os
import csv
import sys

# Parameters
BINS             = 20
PITCH            = 1
NUMBER_OF_VOXELS = 100  # Desired coarse resolution (final grid will have this many voxels on the maximum dimension)
VOXEL_BINNING    = 1
SIZE      = [1,1,1]
SPACING   = [1,1,1]
L_UNITS   = "cm"
CSV_NAME  = "statistics.csv"
verbosity = False
plot      = False

def read_and_produce_image(stl_name, running_on_cluster=False):
    global PITCH, SIZE, SPACING, NUMBER_OF_VOXELS
    if running_on_cluster:
        NUMBER_OF_VOXELS = NUMBER_OF_VOXELS*4 # We increase the finesse since clusters have much more memory

    # Load the STL and compute its bounds and size
    mesh = trimesh.load(stl_name)
    bounds = mesh.bounds  # [[xmin, ymin, zmin], [xmax, ymax, zmax]]
    print("Mesh bounds:", bounds)
    SIZE = bounds[1] - bounds[0]  # Physical size in each dimension

    # Change the resolution: fine grid resolution is *VOXEL_BINNING the desired NUMBER_OF_VOXELS
    fine_number = NUMBER_OF_VOXELS * VOXEL_BINNING
    fine_pitch = np.max(SIZE) / fine_number
    PITCH = fine_pitch

    # Voxelize at the finer resolution
    voxel_grid = mesh.voxelized(pitch=fine_pitch)
    binary_image = voxel_grid.matrix.astype(np.uint8)  # 0 for outside, 1 for STL boundary

    # Fill the interior of the STL
    filled_binary_image = binary_fill_holes(binary_image).astype(np.uint8)
    # Invert so that True (inside) becomes 1
    filled_binary_image = 1 - np.copy(filled_binary_image)
    # Mirror the image (adjust axis order)
    filled_binary_image = np.transpose(np.copy(filled_binary_image), (2, 1, 0))

    # Bin voxels together.
    # This will reduce the resolution by a factor of VOXEL_BINNING in each dimension.
    # block_reduce with np.mean returns the average of each VOXEL_BINNING**3 block.
    # Then we round the fraction to obtain 0 or 1.
    binned_fraction = block_reduce(filled_binary_image, block_size=(VOXEL_BINNING,
                                                                    VOXEL_BINNING,
                                                                    VOXEL_BINNING),
                                                                    func=np.mean)
    binned_binary = np.rint(binned_fraction).astype(np.uint8)

    # Recalculate spacing for the binned image
    SPACING = SIZE / np.array(binned_binary.shape)  # Physical size per coarse voxel
    origin = bounds[0]  # Grid origin matching the STL

    # Create a PyVista StructuredGrid with the binned (coarse) image
    grid = pv.StructuredGrid()
    x = np.arange(origin[0], origin[0] + binned_binary.shape[0] * SPACING[0], SPACING[0])
    y = np.arange(origin[1], origin[1] + binned_binary.shape[1] * SPACING[1], SPACING[1])
    z = np.arange(origin[2], origin[2] + binned_binary.shape[2] * SPACING[2], SPACING[2])
    x, y, z = np.meshgrid(x, y, z, indexing="ij")
    grid.points = np.c_[x.ravel(), y.ravel(), z.ravel()]
    grid.dimensions = binned_binary.shape
    grid["binary"] = binned_binary.flatten(order="F")

    # Save the final VTK file in the same directory as the STL file
    folder = os.path.dirname(os.path.abspath(stl_name))
    vtk_file_path = os.path.join(folder, "binary_image.vtk")
    grid.save(vtk_file_path)
    print(f"Binary image saved as '{vtk_file_path}', with binning applied.")

    return binned_binary  # This is the coarse voxel grid with binary phase values (0 or 1)

# REV (Representative Elementary Volume) Estimation:
# There's no single function called 'rev_estimation' in PoreSpy,
# but we can do a simple approach by checking porosity over subvolumes.
# For demonstration, let's compute porosity over increasing cube sizes and see when it stabilizes.
def rev_estimate(im, step=10):
    shape = np.array(im.shape)
    max_len = np.min(shape)
    rev_data = []
    # Check subcubes of increasing size
    for s in range(step, max_len, step):
        subcube = im[0:s, 0:s, 0:s]
        rev_data.append((s, ps.metrics.porosity(subcube)))
    return rev_data

def moments_of_distribution(x, y, rescale = 1):
    x = x * rescale

    # Normalize the distribution
    y_integral = np.trapz(y,x)
    y_normalized = y / y_integral

    mean   = np.trapz(x * y_normalized,x)

    # Weighted variance
    variance =  np.trapz((x - mean)**2 * y_normalized,x=x)
    std      = variance**0.5

    # Weighted skewness 
    numerator   = np.trapz(((x - mean)**3) * y_normalized,x=x)
    denominator = std**3
    skewness    = numerator / denominator
    
    # Kurtosis
    numerator   = np.trapz(((x - mean)**4) * y_normalized,x=x)
    denominator = std**4
    kurtosis    = numerator / denominator

    return {
        "mean"    : mean,
        "std"     : std,
        "skewness":skewness,
        "kurtosis":kurtosis        
    }

def plot_distribution(distribution, 
                      title="Distribution", 
                      xlabel="X", 
                      ylabel="Y", 
                      rescale = 1, 
                      invert_cdf=False,
                      x_is_log = False):
    plt.figure()
    x = distribution.bin_centers
    if x_is_log:
        x = 10**x
    cdf = distribution.cdf
    if invert_cdf:
        cdf = 1 - cdf
    plt.plot(x*rescale, distribution.pdf, 'o-', label="PDF")
    plt.plot(x*rescale, cdf, '.', label="CDF")
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(loc="best")
    plt.grid(True)
    plt.show()

def porosity(image,dictionary):
    porosity = ps.metrics.porosity(image)
    if verbosity:
        print(f"Porosity: {porosity}")

    # Populate the dictionary
    dictionary["porosity"] = porosity
    return porosity 

def pore_size_distribution(image,dictionary):
    sizes_to_test = np.linspace(0,NUMBER_OF_VOXELS*2,NUMBER_OF_VOXELS*5)
    porosimetry_result = ps.filters.porosimetry(image, 
                                                mode="hybrid", 
                                                access_limited = True, 
                                                sizes=sizes_to_test)
    # Compute the pore size distribution
    psd = ps.metrics.pore_size_distribution(porosimetry_result, bins=BINS)
    if verbosity:
        a = 1
    if plot:
        plot_distribution(psd, title="Pore size", 
                        xlabel     ="Pore Diameter ["+L_UNITS+"]", 
                        ylabel     ="Probability",
                        rescale    = PITCH,
                        invert_cdf =True,
                        x_is_log   =True)
    
    # Populate the dictionary
    temp_dict = moments_of_distribution(10**psd.bin_centers, psd.pdf, rescale= PITCH)
    dictionary["dp_mean"    ] = temp_dict["mean"]
    dictionary["dp_std"     ] = temp_dict["std"]
    dictionary["dp_skewness"] = temp_dict["skewness"]
    dictionary["dp_kurtosis"] = temp_dict["kurtosis"]
    return psd

def chord_length_distribution(image,dictionary):
    chords = ps.filters.apply_chords(image, axis=0)
    cld = ps.metrics.chord_length_distribution(chords, bins=BINS, log=False)
    if verbosity:
        print("Chord Length Distribution (along x-axis):", cld)
    if plot:
        plot_distribution(cld, title="Chord length", 
                        xlabel="Chord length ["+L_UNITS+"]", 
                        ylabel="Probability",
                        rescale    = PITCH,
                        invert_cdf =True)
        
    # Populate the dictionary
    temp_dict = moments_of_distribution(cld.bin_centers, cld.pdf, rescale= PITCH)
    dictionary["cl_mean"    ] = temp_dict["mean"]
    dictionary["cl_std"     ] = temp_dict["std"]
    dictionary["cl_skewness"] = temp_dict["skewness"]
    dictionary["cl_kurtosis"] = temp_dict["kurtosis"]
    return cld

def two_point_correlation(image,dictionary):
    tpcf = ps.metrics.two_point_correlation(image, bins=BINS)
    if verbosity:
        print("Two-point correlation function computed.")
    if plot:
        plt.figure(figsize=(8, 6))
        plt.plot(tpcf.distance*PITCH, tpcf.probability_scaled, marker='o', linestyle='-')
        plt.xlabel("Distance ["+L_UNITS+"]")
        plt.ylabel('Normalized Two-Point Correlation')
        plt.title('Two-Point Correlation Function')
        plt.grid(True)
        plt.show()

    distance = tpcf.distance
    corr = tpcf.probability_scaled

    threshold = 1/np.e
    above_threshold = np.where(corr > threshold)[0]
    if len(above_threshold) > 0:
        idx = above_threshold[-1]
        if idx < len(distance)-1:
            x0, x1 = distance[idx], distance[idx+1]
            y0, y1 = corr[idx], corr[idx+1]
            slope = (y1 - y0) / (x1 - x0)
            correlation_length = x0 + (threshold - y0)/slope
        else:
            correlation_length = distance[-1]
    else:
        correlation_length = 0

    integral_scale = np.trapz(corr, distance)
    if len(distance) > 1:
        slope_at_origin = (corr[1] - corr[0]) / (distance[1] - distance[0])
    else:
        slope_at_origin = np.nan

    dictionary["tpc_length"         ] = correlation_length*PITCH
    dictionary["tpc_integral_scale" ] = integral_scale*PITCH
    dictionary["tpc_slope_at_origin"] = slope_at_origin/PITCH
    return tpcf

def lineal_path_distribution(image,dictionary):
    distance_transform = ps.filters.distance_transform_lin(image)
    lpd = ps.metrics.lineal_path_distribution(distance_transform, bins=BINS, log=False)
    if verbosity:
        print("Lineal Path Distribution :", lpd)
    if plot:
        plot_distribution(lpd, title="Lineal path", 
                        xlabel="Lineal path ["+L_UNITS+"]", 
                        ylabel="Probability",
                        rescale    = PITCH,
                        invert_cdf =True,
                        x_is_log   =False)
        
    temp_dict = moments_of_distribution(lpd.bin_centers, lpd.pdf)
    dictionary["lpd_mean"    ] = temp_dict["mean"]*PITCH
    dictionary["lpd_std"     ] = temp_dict["std"]*PITCH
    dictionary["lpd_skewness"] = temp_dict["skewness"]
    dictionary["lpd_kurtosis"] = temp_dict["kurtosis"]
    return lpd

def radial_density_distribution(image,dictionary):
    dt = ps.filters.distance_transform_lin(image)
    mask = ps.filters.find_dt_artifacts(dt)
    mask = mask.astype(bool)
    dt[mask] = 0
    rdf = ps.metrics.radial_density_distribution(dt, bins=BINS, log=False)

    if verbosity:
        print("Radial Distribution Function computed.")
    if plot:
        plot_distribution(rdf, title="Radial density distribution", 
                        xlabel="Radius ["+L_UNITS+"]", 
                        ylabel="Density",
                        rescale    = PITCH,
                        invert_cdf =True,
                        x_is_log   =False)
        
    temp_dict = moments_of_distribution(rdf.bin_centers, rdf.pdf)
    dictionary["rdf_mean"    ] = temp_dict["mean"]*PITCH
    dictionary["rdf_std"     ] = temp_dict["std"]*PITCH
    dictionary["rdf_skewness"] = temp_dict["skewness"]
    dictionary["rdf_kurtosis"] = temp_dict["kurtosis"]
    return rdf

def euler_characteristic(image,dictionary):
    labeled_im = label(image)
    verts, faces, normals, values = marching_cubes(image, level=0.5)
    V = verts.shape[0]
    F = faces.shape[0]
    print(V)
    print(F)
    edges = set()
    for face in faces:
        for i in range(3):
            edge = tuple(sorted((face[i], face[(i + 1) % 3])))
            edges.add(edge)
    E = len(edges)
    chi = V - E + F

    if verbosity:
        print(f"Euler Characteristic (χ): {chi}")

    dictionary["euler_characteristic"] = chi
    return chi

def tortuosity(image,dictionary,axis=0):
    try:
        tort = ps.simulations.tortuosity_fd(image, axis)
        if verbosity:
            print("Tortuosity estimated:", tort)
        dictionary["tortuosity"+str(axis)] = tort.tortuosity
        return tort
    except Exception as e:
        if verbosity:
            print("Tortuosity estimation not successful:", e)

def medium_statistics(image):
    im = image.astype(bool)
    dictionary = {}
    porosity(im,dictionary)
    pore_size_distribution(im,dictionary)
    chord_length_distribution(im,dictionary)
    two_point_correlation(im,dictionary)
    lineal_path_distribution(im,dictionary)
    radial_density_distribution(im,dictionary)
    euler_characteristic(im,dictionary)
    tortuosity(im,dictionary,axis=0)
    tortuosity(im,dictionary,axis=1)
    tortuosity(im,dictionary,axis=2)

    print(dictionary)
    return dictionary

def run(stl_name, running_on_cluster=False):
    image      = read_and_produce_image(stl_name,running_on_cluster)
    dictionary = medium_statistics(image)
    return dictionary

if __name__ == "__main__":
    if len(sys.argv) > 1:
        argument = sys.argv[1]
        run(argument)
    else:
        print("No argument provided. Please provide one.")
