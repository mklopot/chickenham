import re
import reedsolo


class Batch:
    pattern = re.compile(r'(\d+)/(\d+)-(\d+)')

    def __init__(self, raw_value):
        self.raw_value = raw_value
        self.valid = False
        parsed = self.pattern.search(raw_value)
        if parsed:
            groups = parsed.groups()
            if '' not in groups:
                self.valid = True
                self.sequence = groups[1]
                self.threshold = groups[2]
                self.size = groups[3]

    def __eq__(self, other):
        return self.sequence == other.sequence and
             self.threshold == other.threshold and
             self.size == other.size


class Share:
    rs = reedsolo.RSCodec(20)

    def __init__(self, raw_value, batch):
        self.raw_value = "".join(raw_value.split())
        self.batch = batch
        self.code = ""
        try:
            decoded = rs.decode(bytes.fromhex(self.raw_value))
        except Exception:
            return 
        if len(decoded) == 33:
            as_string = decoded.hex()
            self.code = as_string[0:2] + "-" + as_string[2:]
            

