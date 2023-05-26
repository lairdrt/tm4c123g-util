# Utilities for the TM4C123G
## chtoasms.py
Converts a C .h file (from Texas Instruments - TI) to equivalent ASM .s file.

Intended to process: tm4c123gh6pm.h - TM4C123GH6PM Register Definitions

The file tm4c123gh6pm.h is part of the following from TI:
 
[SW-TM4C TivaWare™ for C Series (Complete)](https://www.ti.com/tool/SW-TM4C)

You can custommize the processing of the C .h file as follows:
```
usage: chtoasms [-h] -i INPUT -o OUTPUT [-nw NAME_WIDTH] [-vw VALUE_WIDTH] [-np NAME_PADDING] [-ep END_PADDING] [-d] [-c] [-s]

Converts a C .h file (from Texas Instruments) to equivalent ASM .s file.

options:
  -h, --help            show this help message and exit
  -i INPUT, --input INPUT
                        specify input file
  -o OUTPUT, --output OUTPUT
                        specify output file
  -nw NAME_WIDTH, --name_width NAME_WIDTH
                        minimum width of name column (32)
  -vw VALUE_WIDTH, --value_width VALUE_WIDTH
                        width of value column (12)
  -np NAME_PADDING, --name_padding NAME_PADDING
                        spaces to add after name (2)
  -ep END_PADDING, --end_padding END_PADDING
                        spaces to add before END command (4)
  -d, --end             output END command
  -c, --comments        output comments
  -s, --stats           output summary stats
```
