import os
import subprocess
import filecmp
import shutil

# --- Function Definitions (Consolidated) ---

def compare_vasp_files(file1_path, file2_path):
    # Compares the content of two files byte-by-byte. Returns True if the files are identical, False otherwise.
    if not os.path.exists(file1_path):
        print(f"Error: File not found at {file1_path}")
        return False
    if not os.path.exists(file2_path):
        print(f"Error: File not found at {file2_path}")
        return False
    return filecmp.cmp(file1_path, file2_path, shallow=False)

def read_incar(filepath):
    # Reads an INCAR file and returns its content as a list of lines.
    if not os.path.exists(filepath):
        print(f"Error: INCAR file not found at {filepath}")
        return None
    with open(filepath, 'r') as f:
        lines = f.readlines()
    return lines

def write_incar(filepath, lines):
    # Writes a list of lines back to an INCAR file.
    with open(filepath, 'w') as f:
        f.writelines(lines)

def modify_incar_tag(incar_lines, tag, value):
    # Modifies or adds a VASP tag in the INCAR file content. Handles comments and ensures proper formatting.
    new_lines = []
    target_tag = tag.strip().upper()
    tag_handled = False # True if we have found and handled this tag (modified, commented, uncommented)

    for line in incar_lines:
        processed_line = line # Default: keep line as is
        stripped_line = line.strip()
        
        # Determine if it's a commented line
        is_commented = stripped_line.startswith('#') or stripped_line.startswith('!')
        
        # Extract the potential tag name from the line (considering it might be commented)
        line_content_for_tag_check = stripped_line
        if is_commented:
            # Temporarily remove initial comment char to check for tag
            line_content_for_tag_check = stripped_line[1:].strip() 
        
        current_tag_in_line = None
        if '=' in line_content_for_tag_check:
            parts_for_tag = line_content_for_tag_check.split('=', 1)
            current_tag_in_line = parts_for_tag[0].strip().upper()
        
        if current_tag_in_line == target_tag and not tag_handled:
            # We found the target tag (either active or commented out) and haven't processed it yet
            
            comment_suffix = ''
            # Preserve original comment at the end of the line, after the value
            if '#' in line:
                comment_suffix = ' #' + line.split('#', 1)[1]
            elif '!' in line:
                comment_suffix = ' !' + line.split('!', 1)[1]

            if value is None:
                # User wants to comment out the tag
                if not is_commented: # Only comment out if it's currently active
                    processed_line = f"# {stripped_line}\n"
                    print(f"Commented out existing INCAR tag: {target_tag}")
                # If already commented, keep it as is (no change)
            else:
                # User wants to set a value, implies uncommenting if necessary
                processed_line = f"{target_tag} = {value}{comment_suffix.rstrip()}\n"
                if is_commented:
                    print(f"Uncommented and modified INCAR tag: {target_tag} = {value}")
                else:
                    print(f"Modified existing INCAR tag: {target_tag} = {value}")
            
            tag_handled = True # Mark this tag as processed

        new_lines.append(processed_line)

    # After the loop, if the tag was not handled (not found and processed), and we are not trying to comment it out, add it.
    if not tag_handled and value is not None:
        new_lines.append(f"{target_tag} = {value}\n")
        print(f"Added new INCAR tag: {target_tag} = {value}")

    return new_lines

# --- VASP Relaxation Loop ---

# Initial change to 'relax' directory
try:
    os.chdir("relax")
    print("Changed directory to 'relax'")
except FileNotFoundError:
    print("Error: 'relax' directory not found. Please create it or check the path.")
    exit(1)
except Exception as e:
    print(f"An error occurred while changing directory: {e}")
    exit(1)

sbatch_file = "submit.sh"
contcar_path = "CONTCAR"
poscar_path = "POSCAR"
max_iterations = 10
iteration_count = 0

while True:
    iteration_count += 1
    print(f"\n--- Starting VASP iteration {iteration_count} ---")

    try:
        result = subprocess.run(
            ["sbatch", "--wait", sbatch_file],
            capture_output=True,
            text=True,
            check=True
        )
        print("VASP job submitted successfully and completed!")
        print(result.stdout)

    except FileNotFoundError:
        print(f"Error: 'sbatch' command not found. Is SLURM installed and in your PATH?")
        break
    except subprocess.CalledProcessError as e:
        print(f"VASP job failed with error: {e.stderr}")
        break
    except Exception as e:
        print(f"An unexpected error occurred during job submission: {e}")
        break

    if not os.path.exists(contcar_path):
        print(f"Error: {contcar_path} not found after job completion. Cannot compare.")
        break
    if not os.path.exists(poscar_path):
        print(f"Warning: {poscar_path} not found. This might be unexpected if it's the input structure.")

    if compare_vasp_files(contcar_path, poscar_path):
        print("CONTCAR and POSCAR are identical. VASP relaxation converged. Exiting loop.")
        break
    else:
        print("CONTCAR and POSCAR are different. Copying CONTCAR to POSCAR for next iteration.")
        try:
            shutil.copyfile(contcar_path, poscar_path)
            print(f"Successfully copied {contcar_path} to {poscar_path}.")
        except Exception as e:
            print(f"Error copying {contcar_path} to {poscar_path}: {e}")
            break

    if iteration_count >= max_iterations:
        print(f"Reached maximum iterations ({max_iterations}). VASP relaxation may not have fully converged. Exiting loop.")
        break

os.chdir("..")
print("Changed directory back to parent.")

# --- SCF Calculation Setup ---

relax_folder = "relax"
scf_folder = "scf"
files_to_copy_to_scf = ["POSCAR", "POTCAR", "INCAR", "KPOINTS", "submit.sh"]

if not os.path.exists(scf_folder):
    os.makedirs(scf_folder)
    print(f"Created directory: {scf_folder}")
else:
    print(f"Directory '{scf_folder}' already exists.")

for filename in files_to_copy_to_scf:
    source_path = os.path.join(relax_folder, filename)
    destination_path = os.path.join(scf_folder, filename)

    if os.path.exists(source_path):
        try:
            shutil.copy2(source_path, destination_path)
            print(f"Copied {filename} from {relax_folder} to {scf_folder}")
        except Exception as e:
            print(f"Error copying {filename}: {e}")
    else:
        print(f"Warning: Source file '{source_path}' not found. Skipping copy.")

print("File copying to 'scf' folder complete.")

incar_path_scf = os.path.join(scf_folder, "INCAR")

print(f"\n--- Modifying INCAR file in {scf_folder} ---")

incar_lines_scf = read_incar(incar_path_scf)

if incar_lines_scf is not None:
    incar_lines_scf = modify_incar_tag(incar_lines_scf, "NSW", 0)
    incar_lines_scf = modify_incar_tag(incar_lines_scf, "IBRION", -1)
    incar_lines_scf = modify_incar_tag(incar_lines_scf, "ISMEAR", -5)
    incar_lines_scf = modify_incar_tag(incar_lines_scf, "SIGMA", 0.05)
    incar_lines_scf = modify_incar_tag(incar_lines_scf, "ISIF", None) # Comment out ISIF for SCF

    try:
        write_incar(incar_path_scf, incar_lines_scf)
        print(f"Successfully updated INCAR file at {incar_path_scf}")
    except Exception as e:
        print(f"Error writing modified INCAR file: {e}")
else:
    print("INCAR modification aborted due to file read error.")

print("--- INCAR modification complete ---")

# --- SCF Job Submission ---

print(f"\n--- Submitting VASP job in {scf_folder} ---")

try:
    os.chdir(scf_folder)
    print(f"Changed directory to '{scf_folder}'")
except FileNotFoundError:
    print(f"Error: '{scf_folder}' directory not found. Cannot submit job.")
    exit(1)
except Exception as e:
    print(f"An error occurred while changing directory: {e}")
    exit(1)

try:
    print(f"Submitting job: sbatch --wait {sbatch_file}")
    result = subprocess.run(
        ["sbatch", "--wait", sbatch_file],
        capture_output=True,
        text=True,
        check=True
    )
    print("SCF VASP job submitted successfully and completed!")
    print("Standard Output:")
    print(result.stdout)
    if result.stderr:
        print("Standard Error:")
        print(result.stderr)

except FileNotFoundError:
    print(f"Error: 'sbatch' command not found. Is SLURM installed and in your PATH?")
except subprocess.CalledProcessError as e:
    print(f"SCF VASP job failed with error (exit code {e.returncode}):")
    print("Standard Output:")
    print(e.stdout)
    print("Standard Error:")
    print(e.stderr)
except Exception as e:
    print(f"An unexpected error occurred during job submission: {e}")

finally:
    os.chdir("..")
    print(f"Changed directory back to parent from '{scf_folder}'.")

print("--- SCF VASP job submission process complete ---")

# --- DOS Calculation Setup ---

dos_folder = "dos"
files_to_copy_to_dos = ["INCAR", "POSCAR", "POTCAR", "KPOINTS", "CHGCAR", "submit.sh"]

print(f"\n--- Preparing for DOS calculation: Copying files to {dos_folder} ---")

if not os.path.exists(dos_folder):
    os.makedirs(dos_folder)
    print(f"Created directory: {dos_folder}")
else:
    print(f"Directory '{dos_folder}' already exists.")

for filename in files_to_copy_to_dos:
    source_path = os.path.join(scf_folder, filename)
    destination_path = os.path.join(dos_folder, filename)

    if os.path.exists(source_path):
        try:
            shutil.copy2(source_path, destination_path)
            print(f"Copied {filename} from {scf_folder} to {dos_folder}")
        except Exception as e:
            print(f"Error copying {filename} to {dos_folder}: {e}")
    else:
        print(f"Warning: Source file '{source_path}' not found. Skipping copy to {dos_folder}.")

print(f"--- File copying to '{dos_folder}' complete ---")

incar_path_dos = os.path.join(dos_folder, "INCAR")

print(f"\n--- Modifying INCAR file in {dos_folder} for DOS calculation ---")

incar_lines_dos = read_incar(incar_path_dos)

if incar_lines_dos is not None:
    incar_lines_dos = modify_incar_tag(incar_lines_dos, "ISTART", 1)
    incar_lines_dos = modify_incar_tag(incar_lines_dos, "ICHARG", 11)
    incar_lines_dos = modify_incar_tag(incar_lines_dos, "LORBIT", 11)
    incar_lines_dos = modify_incar_tag(incar_lines_dos, "EMIN", -16)
    incar_lines_dos = modify_incar_tag(incar_lines_dos, "EMAX", 9)
    incar_lines_dos = modify_incar_tag(incar_lines_dos, "NEDOS", 1000)

    try:
        write_incar(incar_path_dos, incar_lines_dos)
        print(f"Successfully updated INCAR file at {incar_path_dos}")
    except Exception as e:
        print(f"Error writing modified INCAR file for DOS: {e}")
else:
    print("INCAR modification for DOS aborted due to file read error.")

print("--- INCAR modification for DOS complete ---")

# --- DOS Job Submission ---

print(f"\n--- Submitting VASP job in {dos_folder} ---")

try:
    os.chdir(dos_folder)
    print(f"Changed directory to '{dos_folder}'")
except FileNotFoundError:
    print(f"Error: '{dos_folder}' directory not found. Cannot submit job.")
    exit(1)
except Exception as e:
    print(f"An error occurred while changing directory: {e}")
    exit(1)

try:
    print(f"Submitting job: sbatch --wait {sbatch_file}")
    result = subprocess.run(
        ["sbatch", "--wait", sbatch_file],
        capture_output=True,
        text=True,
        check=True
    )
    print("DOS VASP job submitted successfully and completed!")
    print("Standard Output:")
    print(result.stdout)
    if result.stderr:
        print("Standard Error:")
        print(result.stderr)

except FileNotFoundError:
    print(f"Error: 'sbatch' command not found. Is SLURM installed and in your PATH?")
except subprocess.CalledProcessError as e:
    print(f"DOS VASP job failed with error (exit code {e.returncode}):")
    print("Standard Output:")
    print(e.stdout)
    print("Standard Error:")
    print(e.stderr)
except Exception as e:
    print(f"An unexpected error occurred during job submission: {e}")

finally:
    os.chdir("..")
    print(f"Changed directory back to parent from '{dos_folder}'.")

print("--- DOS VASP job submission process complete ---")