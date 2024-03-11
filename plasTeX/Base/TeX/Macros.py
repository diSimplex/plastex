#!/usr/bin/env python

from plasTeX import Command
from plasTeX.Logging import getLogger

# See the TeXbook, page 213
class romannumeral(Command):
    """ Return lowercase roman representation """
    args = 'name:str'
    def invoke(self, tex):
        a = self.parse(tex)
        roman = ""
        n, number = divmod(int(a['name']), 1000)
        roman = "m"*n
        if number >= 900:
            roman = roman + "cm"
            number = number - 900
        while number >= 500:
            roman = roman + "d"
            number = number - 500
        if number >= 400:
            roman = roman + "cd"
            number = number - 400
        while number >= 100:
            roman = roman + "c"
            number = number - 100
        if number >= 90:
            roman = roman + "xc"
            number = number - 90
        while number >= 50:
            roman = roman + "l"
            number = number - 50
        if number >= 40:
            roman = roman + "xl"
            number = number - 40
        while number >= 10:
            roman = roman + "x"
            number = number - 10
        if number >= 9:
            roman = roman + "ix"
            number = number - 9
        while number >= 5:
            roman = roman + "v"
            number = number - 5
        if number >= 4:
            roman = roman + "iv"
            number = number - 4
        while number > 0:
            roman = roman + "i"
            number = number - 1
        return tex.textTokens(roman)
