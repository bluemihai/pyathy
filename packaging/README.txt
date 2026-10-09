pyathy tests your Python program with scenarios written in plain English
(the .feature files in your features/ folder).

Run it from the folder that holds main.py and this pyathy folder:
  python pyathy        run every features/*.feature against main.py
  python pyathy -q     quiet: one line per scenario and the total
  python pyathy -x     stop at the first scenario that fails (also --fail-fast)
  python pyathy --next-failure
                       run the scenarios that failed last time (remembered in
                       .pyathy/last-run.json), stopping at the first that still fails
  python pyathy steps  every step you can use
  python pyathy -h     usage and an example feature

pyathy's own code is in pyathy/pyathy/. lib/ holds the libraries it uses
(pytest, pytest-bdd and theirs); you never need to open it.
