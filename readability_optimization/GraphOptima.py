from external_api import *
from utils import *
import slurm_api
import external_api

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

# Set up configurations
INSTRUCTION_PATH = os.getcwd() + CONFIG["external_api"]["INSTRUCTION_PATH"]

# Extract email configurations
MAIL_FROM = CONFIG["external_api"]["MAIL"]["FROM"]
MAIL_TO = CONFIG["external_api"]["MAIL"]["TO"]
SMTP_SERVER = CONFIG["external_api"]["MAIL"]["SMTP_SERVER"]
SMTP_PORT = CONFIG["external_api"]["MAIL"]["SMTP_PORT"]
KEY_PATH = CONFIG["external_api"]["MAIL"]["KEY_PATH"]

NUM_LAYOUT_GENERATOR = CONFIG["external_api"]["SLURM"]["NUM_LAYOUT_GENERATOR"]
NUM_LAYOUT_EVALUATOR = CONFIG["external_api"]["SLURM"]["NUM_LAYOUT_EVALUATOR"]
NUM_OPTIMIZER = CONFIG["external_api"]["SLURM"]["NUM_OPTIMIZER"]
NUM_EXTERNAL_API = CONFIG["external_api"]["SLURM"]["NUM_EXTERNAL_API"]
UPDATE_INTERVAL = CONFIG["external_api"]["SLURM"]["UPDATE_INTERVAL"]

EVENT_LOG_DISPLAY_LINES = CONFIG["external_api"]["EVENT_LOG_DISPLAY_LINES"]

JOB_HAS_STOPPED = False

start = datetime.datetime.now()

EVENT_LOG = []

JOB_SUBMISSION_COUNTER = 0

SUBMISSION_LOCKED = False

def buffer_monitoring():
    # initialized slurm_header and slurm_data
    slurm_header, slurm_data = slurm_api.get_slurm_jobs_df()

    while True:
        print(
            r"""

 ██████╗ ██████╗  █████╗ ██████╗ ██╗  ██╗ ██████╗ ██████╗ ████████╗██╗███╗   ███╗ █████╗ 
██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██║  ██║██╔═══██╗██╔══██╗╚══██╔══╝██║████╗ ████║██╔══██╗
██║  ███╗██████╔╝███████║██████╔╝███████║██║   ██║██████╔╝   ██║   ██║██╔████╔██║███████║
██║   ██║██╔══██╗██╔══██║██╔═══╝ ██╔══██║██║   ██║██╔═══╝    ██║   ██║██║╚██╔╝██║██╔══██║
╚██████╔╝██║  ██║██║  ██║██║     ██║  ██║╚██████╔╝██║        ██║   ██║██║ ╚═╝ ██║██║  ██║
 ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝        ╚═╝   ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝

"""
        )
        global JOB_SUBMISSION_COUNTER
        global SUBMISSION_LOCKED

        now = datetime.datetime.now()
        up_time = now - start

        # round the uptime to seconds
        up_time = up_time - datetime.timedelta(microseconds=up_time.microseconds)

        # display the uptime, ignore the microseconds
        print("Uptime: " + str(up_time))

        print("Currently Processing: " + CONFIG["layout_generator"]["GRAPHML_FILE"])
        print("Number of layout generator running: " + str(NUM_LAYOUT_GENERATOR))
        print("Number of layout evaluator running: " + str(NUM_LAYOUT_EVALUATOR))
        print("Number of optimizer running: " + str(NUM_OPTIMIZER))

        email_instruction_list = retrieve_file_list(
            startswith="",
            not_startswith=".",
            retrieve_directory=INSTRUCTION_PATH,
            endswith=".email_instruction",
        )
        print("Email buffer: " + str(email_instruction_list))
        execute_email_instruction(email_instruction_list)
        print("Job submission counter: " + str(JOB_SUBMISSION_COUNTER) + " (max: " + str(
            2 + (NUM_LAYOUT_GENERATOR + NUM_LAYOUT_EVALUATOR + NUM_OPTIMIZER)) + ")")

        print("Locked status: " + str(SUBMISSION_LOCKED))

        # convert uptime to seconds
        up_time_seconds = up_time.total_seconds()

        # Every 5 min, check if the total number of submitted jobs is more than
        # 2 * (NUM_LAYOUT_GENERATOR + NUM_LAYOUT_EVALUATOR + NUM_OPTIMIZER)
        # if this is true, then a job failure has occurred. Lock the job submission for 5min
        # every 5 min, decrease the JOB_SUBMISSION_COUNTER by
        # NUM_LAYOUT_GENERATOR + NUM_LAYOUT_EVALUATOR + NUM_OPTIMIZER



        if JOB_SUBMISSION_COUNTER > 2 + (
                NUM_LAYOUT_GENERATOR + NUM_LAYOUT_EVALUATOR + NUM_OPTIMIZER
        ) and not SUBMISSION_LOCKED:
            log_event(
                "Counting too many job failures. Locking job submission for 10 "
                "min to cool down."
            )
            SUBMISSION_LOCKED = True
            lock_starting_time = datetime.datetime.now()
            # email notify the user that the job submission is locked
            external_api.write_instruction(
                "Job submission is locked",
                "Job submission is locked due to too many job failures. Please check the "
                "status of the jobs and unlock the job submission manually.",
                "email_instruction",
            )

        else:
            if up_time_seconds % 300 == 0:
                if SUBMISSION_LOCKED:
                    if (datetime.datetime.now() - lock_starting_time).total_seconds() > 600:
                        log_event("Job submission unlocked after 10 min cooldown.")
                        SUBMISSION_LOCKED = False

                # decrease the JOB_SUBMISSION_COUNTER every 5 min
                JOB_SUBMISSION_COUNTER = max(
                    JOB_SUBMISSION_COUNTER
                    - (NUM_LAYOUT_GENERATOR + NUM_LAYOUT_EVALUATOR + NUM_OPTIMIZER),
                    0,
                )

        # update the slurm_header and slurm_data every UPDATE_INTERVAL seconds
        if up_time_seconds % UPDATE_INTERVAL == 0:
            slurm_header, slurm_data = slurm_api.get_slurm_jobs_df()

        num_generator_to_call = NUM_LAYOUT_GENERATOR - slurm_api.count_jobs_by_name(
            slurm_header, slurm_data, "layout_generator"
        )
        num_evaluator_to_call = NUM_LAYOUT_EVALUATOR - slurm_api.count_jobs_by_name(
            slurm_header, slurm_data, "layout_evaluator"
        )
        num_optimizer_to_call = NUM_OPTIMIZER - slurm_api.count_jobs_by_name(
            slurm_header, slurm_data, "optimizer"
        )

        # if any of the above num is not 0, then we call the function to spawn the jobs
        if (
                num_generator_to_call > 0
                or num_evaluator_to_call > 0
                or num_optimizer_to_call > 0
        ) and not SUBMISSION_LOCKED:
            print("Calling GraphOptima jobs...")
            call_GraphOptima_jobs(
                num_generator_to_call,
                num_evaluator_to_call,
                num_optimizer_to_call,
                slurm_header,
                slurm_data,
            )
            # immediately update the slurm_header and slurm_data after the call
            slurm_header, slurm_data = slurm_api.get_slurm_jobs_df()

        print("\n\n\n")
        print(
            "Current SLURM jobs status (Updated every "
            + str(UPDATE_INTERVAL)
            + " seconds):"
        )
        slurm_api.pretty_print_dataframe(slurm_header, slurm_data)
        print("\n\n\n")
        pretty_print_event_log(EVENT_LOG_DISPLAY_LINES)
        time.sleep(1)
        os.system("clear")


# this function calls sbatch to spawn layout generator, evaluator and optimizer up to 3 input val times
def call_GraphOptima_jobs(
        num_generator_to_call,
        num_evaluator_to_call,
        num_optimizer_to_call,
        slurm_header,
        slurm_data,
):
    # first detect if the "optimization_completed.txt" file exists under the current directory
    # if it does, then we do not need to call the slurm jobs since the optimization job has finished
    global JOB_HAS_STOPPED
    if os.path.exists("optimization_completed.txt") and not JOB_HAS_STOPPED:
        log_event("Optimization completed!")
        log_event("Terminating all GraphOptima jobs")
        slurm_api.terminate_jobs_by_name(slurm_header, slurm_data, "layout_generator")
        slurm_api.terminate_jobs_by_name(slurm_header, slurm_data, "layout_evaluator")
        slurm_api.terminate_jobs_by_name(slurm_header, slurm_data, "optimizer")
        log_event("All GraphOptima jobs terminated")
        JOB_HAS_STOPPED = True
    elif not JOB_HAS_STOPPED:
        global JOB_SUBMISSION_COUNTER
        while (
                num_generator_to_call > 0
                or num_evaluator_to_call > 0
                or num_optimizer_to_call > 0
        ):
            if num_generator_to_call > 0:
                num_generator_to_call -= 1
                if CONFIG["optimizer"]["LAYOUT_GENERATOR"] == "cuGraph":
                    os.system("sbatch sbatch_script_layout_generator.sh")
                    log_event(
                        "Called a cuGraph layout_generator job, "
                        + str(num_generator_to_call)
                        + " left"
                    )
                    JOB_SUBMISSION_COUNTER += 1
                if CONFIG["optimizer"]["LAYOUT_GENERATOR"] == "graph-tool":
                    os.system("sbatch sbatch_script_layout_generator_gt.sh")
                    log_event(
                        "Called a graph-tool layout_generator job, "
                        + str(num_generator_to_call)
                        + " left"
                    )
                    JOB_SUBMISSION_COUNTER += 1
            if num_evaluator_to_call > 0:
                num_evaluator_to_call -= 1
                os.system("sbatch sbatch_script_layout_evaluator.sh")
                log_event(
                    "Called a layout_evaluator job, "
                    + str(num_evaluator_to_call)
                    + " left"
                )
                JOB_SUBMISSION_COUNTER += 1

            if num_optimizer_to_call > 0:
                num_optimizer_to_call -= 1
                os.system("sbatch sbatch_script_optimizer.sh")
                log_event(
                    "Called a optimizer job, " + str(num_optimizer_to_call) + " left"
                )
                JOB_SUBMISSION_COUNTER += 1


# log a new event that consists of timestamp and the event
def log_event(event):
    ct = datetime.datetime.now()
    time_str = str(ct.timestamp())
    EVENT_LOG.append([time_str, event])


# pretty print the last n events with timestamp with format
def pretty_print_event_log(n=5):
    print("Event log:")
    for i in range(max(0, len(EVENT_LOG) - n), len(EVENT_LOG)):
        print(
            str(
                datetime.datetime.fromtimestamp(float(EVENT_LOG[i][0])).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
            )
            + " "
            + str(EVENT_LOG[i][1])
        )


if __name__ == "__main__":
    # slurm_api.load_scipy_stack()
    buffer_monitoring()
