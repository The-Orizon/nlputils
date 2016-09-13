#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Convert GBK PUA codes to corresponding Unicode codepoints.

This program is free software. It comes without any warranty, to
the extent permitted by applicable law. You can redistribute it
and/or modify it under the terms of the Do What The Fuck You Want
To Public License, Version 2, as published by Sam Hocevar. See
http://www.wtfpl.net/ for more details.
'''

gbk_table = str.maketrans((
    '\ue7c7\ue7c8\ue7e7\ue7e8\ue7e9\ue7ea\ue7eb\ue7ec\ue7ed\ue7ee\ue7ef\ue7f0'
    '\ue815\ue816\ue817\ue818\ue819\ue81a\ue81b\ue81c\ue81d\ue81e'
    '\ue81f\ue820\ue821\ue822\ue823\ue824\ue825\ue826\ue827\ue828'
    '\ue829\ue82a\ue82b\ue82c\ue82d\ue82e\ue82f\ue830\ue831\ue832'
    '\ue833\ue834\ue835\ue836\ue837\ue838\ue839\ue83a\ue83b\ue83c'
    '\ue83d\ue83e\ue83f\ue840\ue841\ue842\ue843\ue844\ue845\ue846'
    '\ue847\ue848\ue849\ue84a\ue84b\ue84c\ue84d\ue84e\ue84f\ue850'
    '\ue851\ue852\ue853\ue854\ue855\ue856\ue857\ue858\ue859\ue85a'
    '\ue85b\ue85c\ue85d\ue85e\ue85f\ue860\ue861\ue862\ue863\ue864'), (
    'ḿǹ〾⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻'
    '⺁𠂇𠂉𠃌⺄㑳㑇⺈⺋龴㖞㘚㘎⺌⺗㥮㤘龵㧏㧟㩳㧐龶龷㭎㱮㳠⺧𡗗龸⺪䁖䅟⺮䌷⺳'
    '⺶⺷𢦏䎱䎬⺻䏝䓖䙡䙌龹䜣䜩䝼䞍⻊䥇䥺䥽䦂䦃䦅䦆䦟䦛䦷䦶龺𤇾䲣䲟䲠䲡䱷䲢䴓'
    '䴔䴕䴖䴗䴘䴙䶮龻'
))

gbk_pua_convert = lambda s: s.translate(gbk_table)

if __name__ == '__main__':
    import sys
    for ln in sys.stdin:
        sys.stdout.write(gbk_pua_convert(ln))

