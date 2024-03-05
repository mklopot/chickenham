from termcolor import colored

from share import Batch, Share


class UserInput:
    def __init__(self):
        self.batch = None
        self.shares = []

    def get_valid_batch_number(self):
        while True:
            print("\nEnter " + colored("Batch Number", "grey", "on_yellow") +
                  " for Shared Code " + colored("{}", "blue").format(len(self.shares) + 1))
            print("and press ENTER")
            print(colored("(or just press ENTER to start this batch over)", "cyan"))
            batch_input = input("Batch Number: ")
            if not batch_input:
                return
            batch = Batch(batch_input)
            if not batch.valid:
                print(colored("Invalid Batch Number\n", "red"))
                print(colored("A batch number must contain a number followed by a slash,\n"
                              "another number, followed by a dash, then one more number.\n"
                              "For example: ", "cyan") + colored("5/8-19", "yellow"))
                print("Try again...")
                continue
            if self.batch is not None:
                if batch == self.batch:
                    print(colored("OK", "green"))
                    return batch
                else:
                    print(colored("Non-matching Batch Number\n", "red"))
                    print(colored("All Batch Numbers within a single batch must match.\n"
                                  "If a Shared Code is marked with a "
                                  "non-matching Batch Number,\n"
                                  "do not try to use it as part of this batch.", "cyan"))
                    print("Try again...")
                    continue
            else:
                self.batch = batch
                print(colored("OK", "green"))
                return batch

    def get_share(self):
        while True:
            print("\nEnter " + colored("Shared Code", "grey", "on_yellow") +
                  colored(" {}", "blue").format(
                      len(self.shares)+1) + " and press ENTER")
            share_input = input("Shared Code: ")
            if not share_input:
                continue
            share = Share(share_input, self.batch)
            if not share.code:
                print(colored("Invalid Shared Code", "red"))
                print(colored(" - The code must consist of numbers and letters A thru F.\n"
                              " - The code must be 86 characters long.\n"
                              " - If a letter or number is unreadable, enter your best guess,\n"
                              "     or a zero, instead of that letter or number.", "cyan"))
                print("Try again...\n")
                continue
            else:
                return share

    def input_batch(self):
        print(colored("You will now be asked to enter the Shared Codes and their\n"
              "batch numbers, until you have entered enough codes to combine them.", "blue"))
        while not self.shares:
            self.input_loop()
        return self.shares

    def input_loop(self):
        while True:
            batch_number = self.get_valid_batch_number()
            if not batch_number:
                print(colored("Discarding previously entered Shared Codes and "
                              "starting this batch over...", "red"))
                self.shares = []
                continue

            share = self.get_share()
            if not share:
                print(colored("Discarding previously entered Shared Codes and "
                              "starting this batch over...", "red"))
                continue
            if share not in self.shares:
                self.shares.append(share)
                print(colored("OK", "green"))
            else:
                print(colored("Duplicate Shared Code discarded", "red"))
                print(colored("Enter each Shared Code only once.", "cyan"))

            if self.batch.threshold <= len(self.shares):
                return self.shares
