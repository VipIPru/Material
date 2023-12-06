import os
import string


from . import utils


class Dialog:
    def __init__(self):
        pass

    def input(self, __prompt: str = "", /):
        try:
            answer = input(__prompt)
        except (OSError, EOFError):
            raise

        except KeyboardInterrupt:
            self.answer("Cancelled")
            exit()

        if not answer:
            self.answer("Cancelled")
            exit()

        return [True, answer]

    def answer(self, text: str) -> bool:
        print()
        print(text)
        print()
        return True


def setup_api():
    dialog = Dialog()
    _, api_id = dialog.input("Enter your API ID: ")
    if not _:
        exit()

    if any(char not in string.digits for char in api_id):
        dialog.answer("Invalid API ID!")
        exit()

    _, api_hash = dialog.input("Enter your API Hash: ")
    if not _:
        exit()

    if len(api_hash) != 32 or any(char not in string.hexdigits for char in api_hash):
        dialog.answer("Invalid API Hash!")
        exit()

    with open(os.path.join(utils.get_base_dir(), "api_tokens.txt"), "w") as f:
        f.write(api_id + "\n" + api_hash)
        dialog.answer("API Tokens set.")

    return True