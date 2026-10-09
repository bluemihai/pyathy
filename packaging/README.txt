pyathy tests your Python program with scenarios written in plain English
(the .feature files in your features/ folder).

Run it from the folder that holds main.py and this pyathy folder:
  python pyathy        run every features/*.feature against main.py
  python pyathy -q     quiet: one line per scenario and the total
  python pyathy -h     how to write a feature, and every step you can use

pyathy's own code is in pyathy/pyathy/. lib/ holds the libraries it uses
(pytest, pytest-bdd and theirs); you never need to open it.
