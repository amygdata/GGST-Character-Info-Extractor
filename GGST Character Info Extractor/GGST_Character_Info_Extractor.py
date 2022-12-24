import sys
import argparse
import re

parser = argparse.ArgumentParser(description='Extracts character system and frame data from parsed BBScript')
parser.add_argument("<INPUT FILE>", help="parsed character BBScript file")
parser.add_argument("-m", "--move", help="target move to extract")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
args = parser.parse_args()

MOVE_NAME_MAP = {
    '5P'  : 'NmlAtk5A',
    '6P'  : 'NmlAtk6A',
    '2P'  : 'NmlAtk2A',
    '5K'  : 'NmlAtk5B',
    '2K'  : 'NmlAtk2B',
    '6K'  : 'NmlAtk6B',
    'c.S' : 'NmlAtk5CNear',
    'f.S' : 'NmlAtk5CFar',
    '2S'  : 'NmlAtk2C',
    '5H'  : 'NmlAtk5D',
    '6H'  : 'NmlAtk6D',
    '2H'  : 'NmlAtk2D',
    '5D'  : 'NmlAtk5E',
    '2D'  : 'NmlAtk2E',
    'j.P' : 'NmlAtkAir5A',
    'j.K' : 'NmlAtkAir5B',
    'j.S' : 'NmlAtkAir5C',
    'j.H' : 'NmlAtkAir5D',
    'j.D' : 'NmlAtkAir5E'
}

def map_move_name(move_name: str) -> str:
    if move_name in MOVE_NAME_MAP:

        mapped_name = MOVE_NAME_MAP[move_name]

        if args.verbose:
            print(f'Mapped {move_name} to {mapped_name}')

        return mapped_name

    return move_name

def open_file(input_file_name: str):
    try:
        input_file = open(input_file_name)
    except FileNotFoundError:
        print(f'Could not find {input_file_name}')
        sys.exit()

    return input_file

def get_move_data(character_data: str, move_name: str) -> str:
    regex_pattern = rf"beginState: s32'{move_name}'([.\s\S]*?)endState:"

    if args.verbose:
        print(f'Scanning character data with regex pattern: {regex_pattern}')

    regex = re.compile(regex_pattern)
    regex_match = regex.search(character_data)

    return regex_match.group(0) if regex_match is not None else None

def get_move_framedata(move_data: str) -> str:
    move_data_lines = move_data.splitlines()

    LINE_PREFIXES = ("sprite:", "hit:", "recoveryState:", "attackEndDelay:", "attackOff:")
    
    for line in move_data_lines:
        line = line.strip()
        if line.startswith(LINE_PREFIXES):
            print(line)

    return None

def main():
    input_file_name = vars(args)['<INPUT FILE>']

    input_file = open_file(input_file_name)

    input_file_data = input_file.read()

    input_file.close()

    if(args.move):
        move_name = map_move_name(args.move)
        move_data = get_move_data(input_file_data, move_name)

        if move_data is not None:
            get_move_framedata(move_data)
        else:
            print(f'Move {move_name} not found')
    else:
        print(input_file_data)

if __name__ == "__main__":
    main()
