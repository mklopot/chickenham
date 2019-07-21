from share import Batch, Share


class UserInput:
    def get_valid_batch_number(self):
            while True:
                batch_input = input("Please enter the Batch Number for the shared code "
                                    "and press ENTER\n"
                                    "(or just press ENTER to start this batch over)\n"
                                    "Batch Number: ")
                if not batch_input:
                    return
                batch = Batch(batch_input)
                if not batch.valid:
                    print("The Batch Number you entered is not valid.\n"
                          "A batch number must contain a number followed by a slash,\n"
                          "another number, followed by a dash, then one more number.\n"
                          "For example: 5/8-19.\n"
                          "Try again...")
                    continue
                if self.batch is not None:
                    if batch == self.batch:
                        return batch
                    else:
                        print("The Batch Number you entered does not match "
                              "the previously entered batch numbers.\n "
                              "All Batch Numbers within a single batch must be the same.\n"
                              "If a shared code is marked with a non-matching Batch Number, "
                              "do not try to use it as part of this batch.\n"
                              "Try again...")
                        continue
                else:
                    self.batch = batch
                    return batch

    def get_share(self):
        while True:
            share_input = input("Enter the Shared Code, and press ENTER: ")
            if not share_input:
                continue
            share = Share(share_input, self.batch)
            if not share.code:
                print("The Shared Code you entered is invalid.\n"
                      " - The code must consist of numbers and letters A thru F.\n"
                      " - The code must be 86 characters long.\n"
                      " - If a letter or number is unreadable, enter your best guess, "
                      "or a zero, instead of that letter or number.\n"
                      "Try again...\n")
                continue
            else:
                return share

    def input_batch(self):
        self.batch = None
        self.shares = []
        print("You will now be asked to enter the Shared Codes and their batch numbers,\n"
              "until you have entered enough codes to proceed...")
        while not self.shares:
            self.input_loop()
        return self.shares

    def input_loop(self):
        while True:
            batch_number = self.get_valid_batch_number()
            if not batch_number:
                print("Discarding previously entered Shared Codes and starting this batch over...")
                self.shares = []
                continue

            share = self.get_share()
            if not share:
                print("Discarding previously entered Shared Codes and starting this batch over...")
                continue
            if share not in self.shares:
                self.shares.append(share)
            else:
                print("*** Duplicate discarded ***")

            if self.batch.threshold <= len(self.shares):
                return self.shares
