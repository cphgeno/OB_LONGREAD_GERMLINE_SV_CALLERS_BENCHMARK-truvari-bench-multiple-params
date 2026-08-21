import os
import argparse
from pathlib import Path
import subprocess
import shutil
import shlex
import sys


def run_truvari_params(input_vcf, truth_vcf, name, settings, key, output_dir):
    '''
    Performs truvari bench with custom parameters

    Arguments
    ----------
    input_vcf: str
        The input vcf from the variant caller
    truth_vcf: str
        The truth vcf for that sample
    settings: List[str]
        Settings to use for Truvari bench
    key: str
        Key identifying this parameter set
    output_dir: str
        The output directory where to store the output
    name: str
        The name of the sample that is being analyzed
    '''

    truth_vcf = os.path.realpath(truth_vcf)

    # Create parameter-specific temp directory
    temp_dir = os.path.join(output_dir, f"temp_{key}")

    # Path to Python 3.10 venv
    venv_path = '/opt/py310'
    activate_path = os.path.join(venv_path, 'bin', 'activate')

    # Build activation command correctly
    activate_cmd = f"source {shlex.quote(activate_path)}"

    # Truvari command
    truvari_cmd = [
        'truvari', 'bench',
        '-b', truth_vcf,
        '-c', input_vcf,
        '-o', temp_dir
    ]

    # Add settings correctly
    if settings:
        truvari_cmd.extend(settings)

    # Combine into one shell command
    cmd = f"{activate_cmd} && " + " ".join(
        shlex.quote(c) for c in truvari_cmd
    )

    # Remove previous temp dir if exists
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

    # Run Truvari
    try:
        process = subprocess.run(
            cmd,
            shell=True,
            executable='/bin/bash',
            capture_output=True,
            text=True,
            check=True
        )

        print(process.stdout)
        print(process.stderr)

    except subprocess.CalledProcessError as e:
        with open(os.path.join(output_dir, f"errors_{key}.txt"), "w") as outfile:
            outfile.write(str(e.stdout) + str(e.stderr))
            return False

    # Rename/move output files
    temp_path = Path(temp_dir)
    dest_dir = Path(output_dir)

    for file_path in temp_path.iterdir():
        if file_path.is_file():
            new_name = f"{name}.{key}.{file_path.name}"
            dest_path = dest_dir / new_name
            shutil.move(str(file_path), str(dest_path))

    return True

def main():
    
    parser = argparse.ArgumentParser(description="Perform Truvari bench on a variant calling vcf against a truthset")
    
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Sample name (e.g., 'sample1')."
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        required=True,
        help="Directory where to write the results to."
    )
    parser.add_argument(
        "--variant_calling.vcfs.gz",
        "--variant_calling.svtype.filtered.no.TRA_BND.vcfs.gz",
        dest="variant_calling_vcfs",    # valid Python attribute name
        required=True,
        help="Path to VCF files"
    )
    parser.add_argument(
        "--data.truthset",
        dest="truthset",    # valid Python attribute name
        required=True,
        help="Path to VCF files"
    )
    parser.add_argument(
        "--data.reference",
        dest="data_reference",
        required=True,
        help="Input reference file."
    )

    args = parser.parse_args()

    dict_settings = {
        '0': ["--pctseq", "0.9", "--passonly"],
        '1': ["--pctseq", "0.7", "--passonly"],
        '2': ["--pctseq", "0.5", "--passonly"],
        '3': ["--pctsize", "0.9", "--passonly"],
        '4': ["--pctsize", "0.7", "--passonly"],
        '5': ["--pctseq", "0.9", "--typeignore", "--passonly"],
        '6': ["--pctseq", "0.7", "--typeignore", "--passonly"],
        '7': ["--pctseq", "0.5", "--typeignore", "--passonly"],
        '8': ["--pctsize", "0.9", "--typeignore", "--passonly"],
        '9': ["--pctsize", "0.7", "--typeignore", "--passonly"],
        '10': ["--pctseq", "0.9", "--pctsize", "0.9", "--pctovl", "0.8", "--refdist", "50", "--typeignore", "--passonly"],
        '11': ["--pctseq", "0.9", "--pctsize", "0.9", "--pctovl", "0.8", "--refdist", "50", "--passonly"],
        '12': ["--pctseq", "0", "--typeignore", "--passonly"],
        '13': ["--pctseq", "0.9", "--pctsize", "0", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '14': ["--pctseq", "0.75", "--pctsize", "0", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '15': ["--pctseq", "0.5", "--pctsize", "0", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '16': ["--pctseq", "0.25", "--pctsize", "0", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '17': ["--pctseq", "0", "--pctsize", "0", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '18': ["--pctseq", "0", "--pctsize", "0.9", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '19': ["--pctseq", "0", "--pctsize", "0.75", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '20': ["--pctseq", "0", "--pctsize", "0.5", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '21': ["--pctseq", "0", "--pctsize", "0.25", "--pctovl", "0", "--refdist", "500", "--passonly"],
        '22': ["--pctseq", "0", "--pctsize", "0.25", "--pctovl", "0", "--refdist", "500", "--passonly", "--dup-to-ins"],
        '23': ["--pctseq", "0", "--pctsize", "0.7", "--pctovl", "0", "--refdist", "500", "--passonl", "--dup-to-ins"],
        '24': ["--pctsize", "0.7", "--pctsize", "0.7", "--passonly", "--refdist", "100"],
        '25': ["--pctsize", "0.7", "--pctsize", "0.7", "--passonly", "--refdist", "50"],
        '26': ["--pctseq", "0", "--pctsize", "0.7", "--pctovl", "0", "--refdist", "500", "--passonly"], # original (12) without --typeignore!
        '28': ["--pctseq", "0", "--pctsize", "0.7", "--pctovl", "0", "--refdist", "500", "--passonly", "--dup-to-ins"],
    }

    for key, settings in dict_settings.items():
        status = run_truvari_params(
            args.variant_calling_vcfs,
            args.truthset,
            args.name,
            settings,
            key,
            args.output_dir
        )

    # Create completion flag once all samples have been processed
    if status is True:
        flag_path = Path(args.output_dir) / f"{args.name}_truvari_multiple_params.flag"
        try:
            flag_path.parent.mkdir(parents=True, exist_ok=True)
            flag_path.write_text("completed\n")
            print(f"[INFO] Wrote completion flag: {flag_path}")
        except Exception as e:
            print(f"[ERROR] Failed to write completion flag {flag_path}: {e}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()


