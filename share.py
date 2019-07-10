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
                self.sequence = int(groups[0])
                self.threshold = int(groups[1])
                self.size = int(groups[2])

    def __eq__(self, other):
        return self.sequence == other.sequence and \
             self.threshold == other.threshold and \
             self.size == other.size


class Share:
    rs = reedsolo.RSCodec(10)

    def __init__(self, raw_value, batch):
        raw_value = "".join(raw_value.split())
        self.raw_value = raw_value.replace("-", "")
        self.batch = batch
        self.code = ""
        try:
            decoded = self.rs.decode(bytes.fromhex(self.raw_value))
        except Exception:
            return 
        if len(decoded) == 33:
            as_string = decoded.hex()
            self.code = as_string[0:2] + "-" + as_string[2:]
            

