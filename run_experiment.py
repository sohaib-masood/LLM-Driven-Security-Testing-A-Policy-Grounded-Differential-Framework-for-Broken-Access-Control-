"""One command per target. Always switch the live HMS to the target first.
Usage:
  python run_experiment.py stage2        -> runs Stage 2 once (writes patm_entries.json)
  python run_experiment.py test V1       -> runs the tests against whatever is live now, labeled V1
  python run_experiment.py test M01      -> same, labeled M01
"""
import sys

def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    if sys.argv[1] == "stage2":
        import run_stage2
        run_stage2.run()
    elif sys.argv[1] == "test":
        if len(sys.argv) < 3:
            print("Give a label, e.g.: python run_experiment.py test V1"); return
        import run_tests
        run_tests.run_all(sys.argv[2])
    else:
        print(__doc__)

if __name__ == "__main__":
    main()
