from tomah.account import Account
import pprint


def main():
    t = Account()
    t.regions()
    # t.tokens()
    # print(f"me: {pprint.pp(t.me())}")


if __name__ == "__main__":
    main()
