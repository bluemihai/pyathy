pyathy tests your Python program with scenarios written in plain English
(the .feature files in your features/ folder).

Run it from the folder that holds main.py and this pyathy folder:
  python pyathy        run every features/*.feature against main.py
  python pyathy steps  every step you can use
  python pyathy -h     usage and an example feature

Options (short and long form):
  -q,  --quiet              only one line per scenario and the total
  -ff, --fail-fast          stop at the first scenario that fails
  -nf, --next-failure       run the scenarios that failed last time (remembered in
                            .pyathy/last-run.json), stopping at the first that still fails
  -s,  --solution [FOLDER]  run the features here against ./_solution/main.py, or
                            ./FOLDER/main.py (-s obj2 means _solution-obj2)
  -h,  --help               this help

pyathy's own code is in pyathy/pyathy/. lib/ holds the libraries it uses
(pytest, pytest-bdd and theirs); you never need to open it.
