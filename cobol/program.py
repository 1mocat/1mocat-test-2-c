#!/usr/bin/env python3
"""Python re-implementation of cobol/src/program.cbl (BOOKFORUM)."""

import os

BASE = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(BASE, 'src', 'INPUT.DAT')
ACCOUNTS_PATH = os.path.join(BASE, 'data', 'ACCOUNTS.DAT')
BOOKS_PATH = os.path.join(BASE, 'data', 'BOOKS.DAT')
TRANS_PATH = os.path.join(BASE, 'data', 'TRANSACTIONS.DAT')

ACCOUNT_LEN = 34   # X(4) + X(20) + 9(10)
BOOK_LEN = 28      # X(4) + X(20) + X(4)
TRANS_LEN = 22     # X(4) + 9(10) + X(4) + X(4)
INPUT_LEN = 22     # X(4) + X(4) + X(4) + 9(10)


def parse_num(b):
    s = b.replace(b' ', b'0').decode('ascii', 'replace')
    try:
        return int(s)
    except ValueError:
        return 0


def main():
    try:
        with open(INPUT_PATH, 'rb') as f:
            data = f.read()
    except FileNotFoundError:
        print("Error: Input file is empty")
        return

    if len(data) == 0:
        print("Error: Input file is empty")
        return

    # pad short reads with spaces (line-sequential-like behavior)
    if len(data) < INPUT_LEN:
        data = data + b' ' * (INPUT_LEN - len(data))

    buyer = data[0:4]
    seller = data[4:8]
    book = data[8:12]
    amount = parse_num(data[12:22])

    with open(ACCOUNTS_PATH, 'rb') as f:
        accounts = f.read()
    with open(BOOKS_PATH, 'rb') as f:
        books = f.read()

    buyer_found = False
    seller_found = False
    for i in range(0, len(accounts) - ACCOUNT_LEN + 1, ACCOUNT_LEN):
        aid = accounts[i:i + 4]
        if aid == buyer:
            buyer_found = True
        if aid == seller:
            seller_found = True

    book_found = False
    valid_owner = False
    for i in range(0, len(books) - BOOK_LEN + 1, BOOK_LEN):
        bid = books[i:i + 4]
        if bid == book:
            book_found = True
            owner = books[i + 24:i + 28]
            if owner == seller:
                valid_owner = True

    if not (buyer_found and seller_found and book_found and valid_owner):
        print("Transaction failed due to validation errors")
        return

    # update ACCOUNTS.DAT
    new_accounts = bytearray(accounts)
    for i in range(0, len(new_accounts) - ACCOUNT_LEN + 1, ACCOUNT_LEN):
        aid = bytes(new_accounts[i:i + 4])
        balance = parse_num(bytes(new_accounts[i + 24:i + 34]))
        if aid == buyer:
            balance -= amount
        if aid == seller:
            balance += amount
        balance %= 10 ** 10  # PIC 9(10) unsigned truncation
        new_accounts[i + 24:i + 34] = f"{balance:010d}".encode('ascii')
    with open(ACCOUNTS_PATH, 'wb') as f:
        f.write(bytes(new_accounts))

    # update BOOKS.DAT
    new_books = bytearray(books)
    for i in range(0, len(new_books) - BOOK_LEN + 1, BOOK_LEN):
        bid = bytes(new_books[i:i + 4])
        if bid == book:
            new_books[i + 24:i + 28] = buyer
    with open(BOOKS_PATH, 'wb') as f:
        f.write(bytes(new_books))

    # append to TRANSACTIONS.DAT
    trans_amount = amount % (10 ** 10)
    trans_rec = book + f"{trans_amount:010d}".encode('ascii') + seller + buyer
    with open(TRANS_PATH, 'ab') as f:
        f.write(trans_rec)

    print("Transaction completed successfully")


if __name__ == '__main__':
    main()
