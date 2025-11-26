import subprocess
import threading
import queue

OpenSTA  = "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/sta"
OpenROAD = "/OpenROAD-flow-scripts/tools/install/OpenROAD/bin/openroad"

class STAController:
    def __init__(self, setup_file="setup_sta.tcl"):
        # Start OpenSTA as a persistent background process
        self.proc = subprocess.Popen(
            [OpenSTA, "-no_init"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Start background threads to read stdout
        self.output_queue = queue.Queue()
        self.thread = threading.Thread(target=self._reader_thread)
        self.thread.daemon = True
        self.thread.start()

        # Source setup file
        self.send_cmd(f"source {setup_file}")

    # Creates a background thread that reads OpenSTA output
    def _reader_thread(self):
        for line in self.proc.stdout:
            self.output_queue.put(line.rstrip("\n"))

    # Sends a command to OpenSTA
    def send_cmd(self, cmd):
        self.proc.stdin.write(cmd + "\n")
        self.proc.stdin.flush()

    # Returns a list of all lines with markers
    def read_until(self, markers):
        lines = []
        while True:
            line = self.output_queue.get()
            lines.append(line)
            for m in markers:
                if line.startswith(m):
                    return lines

    # Applies new buffer choices and returns setup and hold slack
    def apply_and_get_slacks(self, solfile="buffers.sol"):
        # Apply buffers
        self.send_cmd(f"apply_buffer_solution {solfile}")

        # Compute timing
        self.send_cmd("compute_worst_slacks")

        # Wait until we get WS_SETUP and WS_HOLD
        lines = self.read_until(["WS_HOLD"])

        setup_slack = None
        hold_slack = None

        for line in lines:
            if line.startswith("WS_SETUP"):
                setup_slack = float(line.split()[1])
            if line.startswith("WS_HOLD"):
                hold_slack = float(line.split()[1])

        return setup_slack, hold_slack

    # Closes OpenSTA Thread
    def close(self):
        self.send_cmd("exit")
        self.proc.wait()
