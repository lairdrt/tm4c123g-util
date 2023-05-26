# Converts a C .h file (from Texas Instruments - TI) to equivalent ASM .s file
# Intended to process: tm4c123gh6pm.h - TM4C123GH6PM Register Definitions
#
# The file tm4c123gh6pm.h is part of the following from TI:
# 
# SW-TM4C TivaWare™ for C Series (Complete)
# https://www.ti.com/tool/SW-TM4C
#
# Lines are formatted like:
#
# #define INT_GPIOA               16          // GPIO Port A
# #define INT_GPIOB               17          // GPIO Port B
#
# Or:
#
# define WATCHDOG0_LOAD_R        (*((volatile uint32_t *)0x40000000))
# define GPIO_PORTA_DATA_BITS_R  ((volatile uint32_t *)0x40004000)

import argparse

DEF_NAME_WIDTH = 32
DEF_VALUE_WIDTH = 12
DEF_NAME_LENGTH_PADDING = 2
DEF_END_LENGTH_PADDING = DEF_NAME_LENGTH_PADDING + 2
DEF_INCLUDE_END = False
DEF_INCLUDE_COMMENTS = False
DEF_INCLUDE_STATS = False

parser = argparse.ArgumentParser(prog='chtoasms', description='Converts a C .h file (from Texas Instruments) to equivalent ASM .s file.')
parser.add_argument('-i', '--input', help='specify input file', type=str, nargs=1, required=True)
parser.add_argument('-o', '--output', help='specify output file', type=str, nargs=1, required=True)
parser.add_argument('-nw', '--name_width', help=f'minimum width of name column ({DEF_NAME_WIDTH})', type=int, nargs=1, default=DEF_NAME_WIDTH)
parser.add_argument('-vw', '--value_width', help=f'width of value column ({DEF_VALUE_WIDTH})', type=int, nargs=1, default=DEF_VALUE_WIDTH)
parser.add_argument('-np', '--name_padding', help=f'spaces to add after name ({DEF_NAME_LENGTH_PADDING})', type=int, nargs=1, default=DEF_NAME_LENGTH_PADDING)
parser.add_argument('-ep', '--end_padding', help=f'spaces to add before END command ({DEF_END_LENGTH_PADDING})', type=int, nargs=1, default=DEF_END_LENGTH_PADDING)
parser.add_argument('-d', '--end', help='output END command', default=DEF_INCLUDE_END, action='store_true')
parser.add_argument('-c', '--comments', help='output comments', default=DEF_INCLUDE_COMMENTS, action='store_true')
parser.add_argument('-s', '--stats', help='output summary stats', default=DEF_INCLUDE_STATS, action='store_true')
args = parser.parse_args()

gbl_input_filename = args.input[0]
gbl_output_filename = args.output[0]
gbl_name_width = args.name_width
gbl_value_width = args.value_width
gbl_name_length_padding = args.name_padding
gbl_end_length_padding = args.end_padding
gbl_include_end = args.end
gbl_include_comments = args.comments
gbl_include_stats = args.stats

def next_token(line, pos):
    if line:
        # Find start char
        c = pos
        while line[c] == ' ':
            c += 1
            if c == len(line):
                # Entire line of spaces (?)
                return '', c
        start = c
        # Find next space
        while line[c] != ' ':
            c += 1
            if c == len(line):
                # Rest of line is filled with chars
                return line[start:], c
        stop = c
        return line[start:stop], c+1
    else:
        return '', None

def next_memref_token(line, pos):
    if line:
        # E.g.:
        # (*((volatile uint32_t *)0x40000000)) or ((volatile uint32_t *)0x40004000)
        #             ^                                     ^
        c1 = line.find(')', pos)
        c2 = line.find(')', c1+1)
        if c1 >= 0 and c2 >= 0:
            return line[c1+1:c2], c2
        else:
            return '', None

def next_comment_token(line, pos):
    if line:
        # E.g.:
        #  // GPIO Interrupt Clear
        # ^
        c1 = line.find('//', pos)
        if c1 >= 0:
            return line[c1+2:], len(line)
        else:
            return '', None

def continuation_comment_line(line, threshold):
    if line:
        wschars = 0
        line = line.expandtabs(4)
        for c in line:
            if c == ' ':
                wschars += 1
            else:
                break
        if wschars > threshold:
            return line.strip().startswith('//')
        else:
            return False

def process_line(line, output=False, output_file=None, comments=False, name_width=None, value_width=None):
    # Get rid of tabs and trailing whitespace
    # Need at least three tokens:
    #define=tkn1, literal=tkn2, value=tkn3
    #define=tkn1, literal=tkn2, memory_reference=tkn4
    name_len = 0
    line = line.expandtabs(1).strip()
    tkn1, pos1 = next_token(line, 0)
    if tkn1.startswith('#define'):
        tkn2, pos2 = next_token(line, pos1)
        if tkn2 and pos2 < len(line):
            tkn3, pos3 = next_token(line, pos2)
            if 'volatile' in tkn3:
                tkn4, pos4 = next_memref_token(line, pos3)
                if tkn4:
                    name_len = len(tkn2)
                    if output:
                        name = tkn2.ljust(name_width, ' ')
                        value = tkn4.ljust(value_width, ' ')
                        output_file.write(name + ' EQU ' + value + '\n')
                else:
                    if output:
                        output_file.write('ERROR: ' + tkn2 + '\n')
            else:
                tkn4, pos4 = next_comment_token(line, pos3)
                name_len = len(tkn2)
                if output:
                    name = tkn2.ljust(name_width, ' ')
                    value = tkn3.ljust(value_width, ' ')
                    if tkn4:
                        output_file.write(name + ' EQU ' + value + ' ;' + tkn4 + '\n')
                else:
                    if output:
                        output_file.write(name + ' EQU ' + value + '\n')
    elif tkn1.startswith('//'):
        if comments:
            tkn2, pos2 = next_comment_token(line, 0)
            if tkn2:
                if output:
                    output_file.write(';' + tkn2 + '\n')
    return name_len

# Open input/output files
try:
    input_file = open(gbl_input_filename, 'r')
except:
    print(f'Cannot open input file ({gbl_input_filename})')
    exit(1)
try:
    output_file = open(gbl_output_filename, 'w')
except:
    print(f'Cannot open output file ({gbl_output_filename})')
    exit(1)

# Read input file
lines = input_file.readlines()
input_file.close()

# FIRST PASS: bring continued lines together
nlidx = 0
newline = ''
building_continuation_line = False
building_comment_line = False
numlines = len(lines)
newlines = []
MIN_LEADING_SPACES_FOR_COMMENT = 20
for i in range(numlines):
    line = lines[i].rstrip()
    # Process continuation lines first
    if line.endswith('\\'):
        # Add this one to next line(s)
        building_continuation_line = True
        newline += line[:-1]
    elif building_continuation_line:
        # All done processing continuation lines
        newline += line
        newlines.append(newline)
        nlidx += 1
        building_continuation_line = False
        newline = ''
    # Process continued comment lines next
    elif continuation_comment_line(line, MIN_LEADING_SPACES_FOR_COMMENT):
        # Add this one to previous line(s)
        building_comment_line = True
        newlines[nlidx-1] += line.lstrip()[2:]
    elif building_comment_line:
        # All done processing continuation lines
        building_comment_line = False
        newlines.append(line.lstrip())
        nlidx += 1
    else:
        # Process non-continuation/non-comment lines
        newlines.append(line.lstrip())
        nlidx += 1

# SECOND PASS: find maximum literal name length
max_name_len = 0
for line in newlines:
    name_len = process_line(line)
    max_name_len = max(max_name_len, name_len)

# THIRD PASS: output lines
if gbl_include_stats:
    output_file.write(';\n')
    output_file.write('; Maximum name length: ' + str(max_name_len) + '\n')
    output_file.write('; Combined line count: ' + str(len(newlines)) + '\n')
    output_file.write(';\n')
gbl_name_width = max(gbl_name_width, max_name_len)
for line in newlines:
    process_line(line, output=True, output_file=output_file, comments=gbl_include_comments, name_width=gbl_name_width, value_width=gbl_value_width)
if gbl_include_end:
    output_file.write(';\n')
    output_file.write('END'.rjust(gbl_name_width + gbl_end_length_padding, ' ') + '\n')
