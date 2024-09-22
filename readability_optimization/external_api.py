"""
This module is responsible for monitoring the instruction buffer and executing the instructions in the buffer.
Similar to the layout generator and evaluator, this module also relies on file I/O to communicate with the other
modules. The instructions are written to a file in the instruction buffer, and this module will read the instructions
from the buffer and execute them.
Note this module doesn't have the same filelock implementation as the layout generator and evaluator, as we only expect
to have one instance of this module running at any given time, thus no racing condition is expected.
"""

import smtplib
import time
from dot_to_readability_score import retrieve_file_list
import datetime
import os
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load configuration from JSON file
with open("config.json") as f:
    CONFIG = json.load(f)

# Extract configurations for external_api
CONFIG = CONFIG["external_api"]

# Set up configurations
INSTRUCTION_PATH = os.getcwd() + CONFIG["INSTRUCTION_PATH"]

# Extract email configurations
MAIL_FROM = CONFIG["MAIL"]["FROM"]
MAIL_TO = CONFIG["MAIL"]["TO"]
SMTP_SERVER = CONFIG["MAIL"]["SMTP_SERVER"]
SMTP_PORT = CONFIG["MAIL"]["SMTP_PORT"]
KEY_PATH = CONFIG["MAIL"]["KEY_PATH"]


def buffer_monitoring():
    while True:
        print(
            r"""
$$$$$$$$\             $$\          $$$$$$\  $$$$$$$\ $$$$$$\           
$$  _____|            $$ |        $$  __$$\ $$  __$$\\_$$  _|          
$$ |      $$\   $$\ $$$$$$\       $$ /  $$ |$$ |  $$ | $$ |   $$$$$$$\ 
$$$$$\    \$$\ $$  |\_$$  _|      $$$$$$$$ |$$$$$$$  | $$ |  $$  _____|
$$  __|    \$$$$  /   $$ |        $$  __$$ |$$  ____/  $$ |  \$$$$$$\  
$$ |       $$  $$<    $$ |$$\     $$ |  $$ |$$ |       $$ |   \____$$\ 
$$$$$$$$\ $$  /\$$\   \$$$$  |$$\ $$ |  $$ |$$ |     $$$$$$\ $$$$$$$  |
\________|\__/  \__|   \____/ \__|\__|  \__|\__|     \______|\_______/ 



"""
        )
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("")
        l = []
        for x in os.listdir(INSTRUCTION_PATH):
            l.append(x)
        print(l)
        print("Current Time = " + current_time)
        email_instruction_list = retrieve_file_list(
            startswith="",
            not_startswith=".",
            retrieve_directory=INSTRUCTION_PATH,
            endswith=".email_instruction",
        )
        slurm_instruction_list = retrieve_file_list(
            startswith="",
            not_startswith=".",
            retrieve_directory=INSTRUCTION_PATH,
            endswith=".slurm_instruction",
        )
        print("Email buffer: " + str(email_instruction_list))
        print("Slurm buffer: " + str(slurm_instruction_list))

        execute_email_instruction(email_instruction_list)
        execute_slurm_instruction(slurm_instruction_list)

        time.sleep(1)
        os.system("clear")


def execute_slurm_instruction(slurm_instruction_list):
    if slurm_instruction_list:
        slurm_instruction_content = open(
            INSTRUCTION_PATH + slurm_instruction_list[0], "r"
        ).readlines()

        # if the slurm instruction starts with SBATCH, then run the content of the instruction using os.system
        if slurm_instruction_content[0].startswith("SBATCH"):
            os.system(slurm_instruction_content[0])

        try:
            os.system("rm " + str(INSTRUCTION_PATH + slurm_instruction_list[0]))
        except:
            print("Sync error encountered!")


def execute_email_instruction(email_instruction_list):
    if email_instruction_list:
        instruction_content = open(
            INSTRUCTION_PATH + email_instruction_list[0], "r"
        ).readlines()
        try:
            subject = instruction_content[0]
            message = instruction_content[1]
        except:
            subject = "GraphOptima Notification"
            message = "No message provided"
        send_email_notification(subject=subject, message=message)
        try:
            os.system("rm " + str(INSTRUCTION_PATH + email_instruction_list[0]))
        except:
            print("Sync error encountered!")


def send_email_notification(subject, message):
    """
    Send an email notification using the given subject and message
    """
    msg = MIMEMultipart()
    msg["From"] = MAIL_FROM
    msg["To"] = MAIL_TO
    msg["Subject"] = subject
    msg.attach(MIMEText(message))

    mailserver = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
    # identify ourselves
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    key = None
    try:
        key = open(KEY_PATH, "r").readlines()
    except FileNotFoundError:
        print(
            "Key file not found! Either disable the email notification in the config.json or provide the password to "
            "SMTP as the key file. To change what SMTP to use, go to config[external_api][MAIL]."
        )
    mailserver.login(MAIL_FROM, key[0].strip("\n"))
    mailserver.sendmail(MAIL_FROM, MAIL_TO, msg.as_string())

    mailserver.quit()


def write_instruction(subject: str, message: str, instruction_type: str):
    ct = datetime.datetime.now()
    time_str = str(ct.timestamp())
    with open(INSTRUCTION_PATH + time_str + "." + instruction_type, "w") as f:
        f.write(f"{subject}\n")
        f.write(f"{message}\n")


if __name__ == "__main__":
    # slurm_api.load_scipy_stack()
    buffer_monitoring()
