import signac
from flow import FlowProject
import datetime
from ase.io import read
import numpy as np

class Project(FlowProject):
    pass 

@Project.label
def rep_calculated(job):
    return job.isfile("rep.mts")
# @Project.label
# def result_calculated(job):
#     return "result" in job.document

# @Project.post(lambda job: "result" in job.document)
# @Project.operation
# def perform_calculation(job):
#     print(f"Hi from {job.id}")
#     job.document.result = str(datetime.datetime.now())
#     print("Done!")

@Project.post(lambda job: job.isfile("rep.mts"))
@Project.operation
def calculate_anisoap(job):
    frames = read("frames_1000.xyz", ":")
    print(job.sp)
    for frame in frames:
        # Fix the c_diameter
        frame.arrays["c_diameter[1]"] = frame.arrays.pop("c_diameter1")
        frame.arrays["c_diameter[2]"] = frame.arrays.pop("c_diameter2")
        frame.arrays["c_diameter[3]"] = frame.arrays.pop("c_diameter3")
        curr_positions = frame.get_positions()
        curr_positions[job.sp.atom_i, job.sp.grad_dir] += job.sp.delta
        frame.set_positions(curr_positions)

    if job.sp.rep_type == 'anisoap':
        lmax=4
        nmax=5
        AniSOAP_HYPERS = {
            "max_angular": lmax,
            "max_radial": nmax,
            "radial_basis_name": "gto",
            "rotation_type": "quaternion",
            "rotation_key": "c_q",
            "cutoff_radius": 7.0,
            "radial_gaussian_width": 1.5,
            "basis_rcond": 1e-8,
            "basis_tol": 1e-4,
        }
        from anisoap.representations import EllipsoidalDensityProjection
        calculator = EllipsoidalDensityProjection(**AniSOAP_HYPERS)
        mvg_coeffs = calculator.transform(frames)
        from anisoap.utils.metatensor_utils import (
            ClebschGordanReal,
            cg_combine,
            standardize_keys,
        )
        import metatensor

        mvg_nu1 = standardize_keys(mvg_coeffs)  # standardize the metadata naming schemes
        # Create an object that stores Clebsch-Gordan coefficients for a certain lmax:
        mycg = ClebschGordanReal(lmax)

        # Combines the mvg_nu1 with itself using the Clebsch-Gordan coefficients.
        # This combines the angular and radial components of the sample.
        mvg_nu2 = cg_combine(
            mvg_nu1,
            mvg_nu1,
            clebsch_gordan=mycg,
            lcut=0,
            other_keys_match=["types_center"],
        )
        metatensor.save(job.fn("rep.mts"), mvg_nu2)

    elif job.sp.rep_type == 'soap':
        lmax=4
        nmax=6

        from featomic.calculators import SoapPowerSpectrum
        import metatensor
        HYPER_PARAMETERS = {
            "cutoff": {
                "radius": 5.0,
                "smoothing": {"type": "ShiftedCosine", "width": 0.5},
            },
            "density": {
                "type": "Gaussian",
                "width": 0.3,
            },
            "basis": {
                "type": "TensorProduct",
                "max_angular": lmax,
                "radial": {"type": "Gto", "max_radial": nmax},
            },
        }

        calculator = SoapPowerSpectrum(**HYPER_PARAMETERS)
        descriptor = calculator.compute(frames, gradients=['positions'])
        metatensor.save(job.fn("rep.mts"), descriptor)

    

if __name__ == "__main__":
    Project().main()