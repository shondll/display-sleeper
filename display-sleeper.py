#!/usr/bin/env python3

"""An simple script to handle display off in Linux with Chrome based browser that has a bug and prevents that
"""

import getopt
import sys
import logging
from enum import IntEnum
import time
import pyautogui
import subprocess


logger = logging.getLogger(__name__)

class State(IntEnum):
    INIT = 0
    MONITORING = 1
    FORCE_MONITOR_SLEEP = 2,
    WAIT_MOVEMENT = 3

def bash_exec(command):
    logger.debug("Executing: {}".format(' '.join(command)))
    proc = subprocess.Popen(command, bufsize=4096, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buf, errbuf = proc.communicate()
    ret = proc.wait()

    logger.debug("Exit code: {}, stderr: {}".format(ret, errbuf))

    return ret, buf

########################
# Main entry
########################

def usage():
    usage_str = """Usage:
        {0} -d <tty_file> [-d <tty_file>] ...
    Where:
        -h, --help
            print this help
        -d, --debug
            print debug logs
        -t, --timeout
            timeout value in s""".format(sys.argv[0])
    print(usage_str)


def main(argv):
    debug_mode = False
    off_time_sec = 600

    try:
        opts, args = getopt.getopt(argv, "hdt:", ["help", "debug", "timeout"])
    except getopt.GetoptError:
        usage()
        sys.exit(-1)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-d", "--debug"):
            debug_mode = True
        elif opt in ("-t", "--timeout"):
            off_time_sec = int(arg)

    if debug_mode:
        logging.basicConfig(level='DEBUG')
    else:
        logging.basicConfig(level='INFO')

    logger.info(">>> The display sleeper has started with timeout of {}s! <<<".format(off_time_sec))

    ########
    # The endless loop
    state = State.INIT
    while True:
        if state == State.INIT:
            last_pos = pyautogui.position()
            last_movement_ts = time.time()
            state = State.MONITORING

        elif state == State.MONITORING:
            curr_pos = pyautogui.position()
            now = time.time()
            if curr_pos != last_pos:
                last_movement_ts = now
                last_pos = curr_pos
                logger.debug("Movement detected, reset timer")

            inactivity_period = now - last_movement_ts
            logger.debug("No movement detected for {}s".format(inactivity_period))
            if inactivity_period > off_time_sec:
                state = State.FORCE_MONITOR_SLEEP

        elif state == State.FORCE_MONITOR_SLEEP:
            logger.info("Forcing monitor sleep now")
            bash_exec(['xset', 'dpms', 'force', 'off'])

            last_pos = pyautogui.position()
            state = State.WAIT_MOVEMENT

        elif state == State.WAIT_MOVEMENT:
            curr_pos = pyautogui.position()
            if curr_pos != last_pos:
                logger.debug("Movement detected, starting over")
                state = State.INIT

        time.sleep(1)

        logger.debug("Bot in state {}".format(state.name))


if __name__ == "__main__":
	main(sys.argv[1:])
