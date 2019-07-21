import subprocess


class Combiner:
    def __init__(self, threshold, hex=True):
        self.threshold = threshold
        self.hex = hex

    def __call__(self, shares_list):
        if len(shares_list) < self.threshold:
            raise ValueError("Not enough shares to meet threshold")
        cmd = ['ssss-combine', '-t{}'.format(self.threshold)]
        if self.hex:
            cmd.append('-x')
        process = subprocess.Popen(cmd,
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   universal_newlines=True)
        stdout, stderr = process.communicate(input="\n".join(shares_list))
        output = stdout + '\n' + stderr
        output_list = output.split("\n")
        for line in output_list:
            if "Resulting secret: " in line:
                return line.split(" ")[-1]
