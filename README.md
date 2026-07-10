--- HOW TO RUN VASP AUTOMATED ---

  This code is to run VASP from relaxation to density of states calculation. It is made specifically to run on slurm. 

  To run this code, you will need the following:
    1. A POSCAR file - generate this with VESTA using your cif file
    2. An INCAR file
    3. A POTCAR file - generate this specific to your POSCAR
    4. A KPOINTS file
    5. A job submission script - title it 'submit.sh' for this script

  How to setup:
    1. Create a project 'home' folder for your material.
    2. Within the project folder, create a folder titled 'relax'.
    3. In this relaxation folder, upload the five files listed above. Return to your home folder.
    4. Run this script in the home folder, and you're done!
