
from scripts.generate_benchmarks import generate
from scripts.simulate_algorithm import simulate
from scripts.export_database import export
from scripts.import_database import import_


def main():
    print('\nWelcome in RCEMP Scrips')
    print('=' * 50)
    running = True
    while running:
        print('You can do following actions:')
        print('\t1. generate banchmarks')
        print('\t2. simulate algorithm')
        print('\t3. export benchmark data')
        print('\t4. import benchmark data')
        print('\t5. exit this program (Ctrl+C)')
        choice = int(input('Type your choice: '))
        if choice == 1:
            generate()
        elif choice == 2:
            simulate()
        elif choice == 3:
            export()
        elif choice == 4:
            import_()
        else:
            running = False

if __name__ == '__main__':
    main()