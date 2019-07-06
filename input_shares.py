from shares import Batch, Share

class UserInput:
    def get_valid_batch_number(self):
            while True
                batch_input = input("Please enter the Batch Number for the shared code, and press ENTER (or just press ENTER to start this batch over): ")          
                if batch_input == "":
                    return
                batch = Batch(first_batch_input)
                if not self.batch.valid:
                    print("The Batch Number you entered is not valid. A batch number must contain a number followed by a slash, "
                          "another number folowed by a dash, then one more number, for example: 5/8-19. Try again."
                    continue
                if self.batch is not None:
                    if batch == self.batch:
                        return batch
                    else:
                        print("The Batch Number you entered does not match the previously entered batch numbers. "
                              "All batch numbers within a single batch must be the same.\nTry again.")
                        continue
                else:
                    self.batch = batch
                    return batch

    def get_share(self):
        while True:
            share_input = input("Enter the Shared Code, and press ENTER: ")
            if not share_input:
                return
            share = Share(share_input, self.batch)
            if not share.code:
                print("The Shared Code you entered is invalid. \n"
                      " - The code must consist of numbers and letters A thru F.\n "
                      " - The code must be 86 characters long.\n"
                      " - If a letter or number is unreadable, enter your best guess, or a zero, instead of that letter or number."
                      "Try again.") 
                continue
            self.shares.append(share)
               
    def input_batch(self):
        while True:
            self.batch = None
            self.shares = []
            print("You will now be asked to enter the Shared Codes along with their batch numbers, until you have entered enough codes to proceed...")

            batch_number = self.get_valid_batch_number() 
            if not batch_number:
                print("Discarding previously entered Shared Codes and starting this entire batch over..."
                continue

            share = self.get_share()
            if not share:
                print("Discarding previously entered Shared Codes and starting this entire batch over..."
                continue
            self.shares.append(share)

            if batch.threshold <= len(self.shares)
                return shares 
