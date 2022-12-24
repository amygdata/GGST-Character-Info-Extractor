import sys
import argparse
import re

parser = argparse.ArgumentParser(description='Extracts character system and frame data from parsed BBScript')
parser.add_argument("<INPUT FILE>", help="parsed character BBScript file")
parser.add_argument("-m", "--move", help="target move to extract")
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
args = parser.parse_args()

class Move:
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

    def __init__(self, move_data: str, move_alias = None):
        self.data = move_data
        self.move_name = None
        self.move_alias = move_alias

        self.startup_frames = 0
        self.active_frames = 0
        self.recovery_frames = 0

        self.damage = []
        self.attack_level = []
        self.counter_type = 0

        self.set_move_name()

        if self.move_alias is None:
            self.set_move_alias()

        self.get_move_damage()
        self.get_move_attack_level()
        self.get_move_counter_type()
        self.get_move_framedata()

    def set_move_name(self):
        regex_match = re.search(r"beginState: s32'(.+)'", self.data)

        if regex_match is not None:
            self.move_name = regex_match.group(1)

            if args.verbose:
                print(f'Found move name {self.move_name}')

    def set_move_alias(self):
        for alias, name in self.MOVE_NAME_MAP.items():
            if name == self.move_name:
                self.move_alias = alias

                if args.verbose:
                    print(f'Mapped name {self.move_name} to alias {self.move_alias}')

    def get_move_damage(self):
        regex = re.compile(r"damage: \d+, (\d+)")

        for line in self.data.splitlines():
            match = regex.search(line.strip())

            if match is not None:
                self.damage.append(int(match.group(1)))
        
        print(f'Damage {self.damage}')

    def get_move_attack_level(self):
        match = re.search(r"_AtkLv(\d)", self.data)

        if match is not None:
            self.attack_level.append(int(match.group(1)))
            print(f'Attack Level {self.attack_level}')

    def get_move_counter_type(self):
        match = re.search(r"_countertype'", self.data)

        if match is not None:
            self.counter_type = "Small"

        match = re.search(r"_countertype_m", self.data)

        if match is not None:
            self.counter_type = "Mid"

        match = re.search(r"_countertype_h", self.data)

        if match is not None:
            self.counter_type = "Large"

        print(f'Counter Type {self.counter_type}')

    def get_move_framedata(self):
        move_data_lines = self.data.splitlines()

        RECOVERY_PREFIXES = (
            "recoveryState:", 
            "attackEndDelay:", 
            "attackOff:",
            "callSubroutine: s32'cmn_AttackEnd'",
        )

        EARLY_RECOVERY_CANCEL_PREFIXES = (
            "callSubroutine: s32'cmnNandemoCancel'", #Cancel recovery early
            "callSubroutine: s32'cmnNandemoCancelA'",
            "callSubroutine: s32'cmnNandemoCancelC'",
        )

        LINE_PREFIXES = (
            "sprite:", 
            "hit:", 
        ) + RECOVERY_PREFIXES + EARLY_RECOVERY_CANCEL_PREFIXES

        current_stage = 0

        for line in move_data_lines:
            line = line.strip()

            if line.startswith(LINE_PREFIXES):
                #print(line)

                if line.startswith("sprite:"):
                    sprite_name, sprite_time = self._get_sprite_info(line)

                match current_stage:
                    case 0:
                        if line.startswith("hit:"):
                            self.startup_frames -= sprite_time - 1
                            self.active_frames += sprite_time
                            current_stage = 1
                        else:
                            self.startup_frames += sprite_time
                    case 1:
                        if line.startswith(RECOVERY_PREFIXES):
                            self.active_frames -= sprite_time
                            self.recovery_frames += sprite_time
                            current_stage = 2
                        else:
                            if line.startswith("sprite:"):
                                self.active_frames += sprite_time
                    case 2:
                        if line.startswith("hit:"):
                            self.active_frames += self.recovery_frames 
                            self.recovery_frames = 0
                            current_stage = 1
                        elif line.startswith(EARLY_RECOVERY_CANCEL_PREFIXES):
                            self.recovery_frames -= sprite_time
                            break
                        else:
                            self.recovery_frames += sprite_time

        print(f'Total Startup: {self.startup_frames}')
        print(f'Total Active Time: {self.active_frames}')
        print(f'Total Recovery Time: {self.recovery_frames}')

    @staticmethod
    def _get_sprite_info(sprite_data: str) -> tuple[str, int]:
        regex_match = re.search(r"'(.+)', (\d+)", sprite_data)

        return regex_match.group(1), int(regex_match.group(2)) if regex_match is not None else None

    @staticmethod
    def map_move_alias(move_alias: str) -> str:
        if move_alias in Move.MOVE_NAME_MAP:

            mapped_name = Move.MOVE_NAME_MAP[move_alias]

            if args.verbose:
                print(f'Mapped alias {move_alias} to name {mapped_name}')

            return mapped_name

        return None

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


def main():
    input_file_name = vars(args)['<INPUT FILE>']

    input_file = open_file(input_file_name)

    input_file_data = input_file.read()

    input_file.close()

    if(args.move):
        move_name = Move.map_move_alias(args.move)

        move_data = None
        if move_name is not None:
            move_data = get_move_data(input_file_data, move_name)
        else:
            move_data = get_move_data(input_file_data, args.move)

        if move_data is not None:
            move = Move(move_data)
        else:
            if move_name is not None:
                print(f'Move {move_name} not found')
            else:
                print(f'Move {args.move} not found')
    else:
        print(input_file_data)

if __name__ == "__main__":
    main()
