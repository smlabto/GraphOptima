import subprocess
import getpass


def get_slurm_jobs_df():
    current_user = getpass.getuser()
    cmd = ["squeue", "-o", "%i,%j,%u,%T,%M,%l,%D,%R,%S,%V,%Z", "-u", current_user]
    output = subprocess.check_output(cmd, text=True)

    lines = output.split("\n")
    header_line = lines[0]
    headers = header_line.split(",")

    job_list = []
    for line in lines[1:]:
        if not line.strip():
            continue
        job_data = line.split(",")
        if len(job_data) != len(headers):
            continue
        job_dict = {
            headers[i].strip(): job_data[i].strip() for i in range(len(headers))
        }
        job_list.append(job_dict)

    return headers, job_list


def pretty_print_dataframe(headers, data):
    max_widths = [len(header) for header in headers]
    for row in data:
        for i, header in enumerate(headers):
            max_widths[i] = max(max_widths[i], len(row[header]))

    format_str = " | ".join([f"{{:<{width}}}" for width in max_widths])
    separator = "-+-".join(["-" * width for width in max_widths])

    print(format_str.format(*headers))
    print(separator)
    for row in data:
        print(format_str.format(*[row[header] for header in headers]))


def load_scipy_stack():
    cmd = "module load scipy-stack/2021a"
    output = subprocess.check_output(cmd, shell=True, text=True)
    return output


def count_jobs_by_name(headers, job_list, job_name):
    count = 0
    for job in job_list:
        if job["NAME"] == job_name:
            count += 1

    return count


# terminate all jobs with a given name and is owned by the current user
def terminate_jobs_by_name(headers, job_list, job_name):
    for job in job_list:
        if job["NAME"] == job_name:
            cmd = f"scancel {job['JOBID']}"
            output = subprocess.check_output(cmd, shell=True, text=True)
            print(output)


if __name__ == "__main__":
    load_scipy_stack()
    headers, data = get_slurm_jobs_df()
    pretty_print_dataframe(headers, data)
