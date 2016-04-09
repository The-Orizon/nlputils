#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import itertools

'''
Various functions for processing Chinese text.
'''

halfwidth = frozenset('!(),:;?')
fullwidth = frozenset(itertools.chain(
    range(0xFF02, 0xFF07 + 1),
    (0xFF0A, 0xFF0B, 0xFF0E, 0xFF0F, 0xFF1C, 0xFF1D,
     0xFF1E, 0xFF3C, 0xFF3E, 0xFF3F, 0xFF40),
    range(0xFF10, 0xFF19 + 1),
    range(0xFF20, 0xFF3A + 1),
    range(0xFF41, 0xFF5A + 1)))
resentencesp = re.compile('([﹒﹔﹖﹗．；。！？]["’”」』]{0,2}|：(?=["‘“「『]{1,2}|$))')
refixmissing = re.compile(
    '(^[^"‘“「『’”」』，；。！？]+["’”」』]|^["‘“「『]?[^"‘“「『’”」』]+[，；。！？][^"‘“「『‘“「『]*["’”」』])(?!["‘“「『’”」』，；。！？])')

punctstr = (
    '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~¢£¥·ˇˉ―‖‘’“”•′‵、。々'
    '〈〉《》「」『』【】〔〕〖〗〝〞︰︱︳︴︵︶︷︸︹︺︻︼︽︾︿﹀﹁﹂﹃﹄'
    '﹏﹐﹒﹔﹕﹖﹗﹙﹚﹛﹜﹝﹞！（），．：；？［｛｜｝～､￠￡￥')

punct = frozenset(punctstr)

whitespace = ' \t\n\r\x0b\x0c\u3000'

resplitpunct = re.compile('([%s])' % re.escape(punctstr))

tailpunct = ('''!),-.:;?]}¢·ˇˉ―‖’”•′■□△○●'''
             '''、。々〉》」』】〕〗〞︰︱︳︴︶︸︺︼︾﹀﹂﹄﹏'''
             '''﹐﹒﹔﹕﹖﹗﹚﹜﹞！），．：；？｜］｝～､￠''') + whitespace
headpunct = ('''([`{£¥‘“〈《「『【〔〖〝'''
             '''︵︷︹︻︽︿﹁﹃﹙﹛﹝（［｛￡￥''') + whitespace

openbrckt = ('([{（［｛⦅〚⦃“‘‹«「〈《【〔⦗『〖〘｢⟦⟨⟪⟮⟬⌈⌊⦇⦉❛❝❨❪❴❬❮❰❲'
             '⏜⎴⏞〝︵⏠﹁﹃︹︻︗︿︽﹇︷〈⦑⧼﹙﹛﹝⁽₍⦋⦍⦏⁅⸢⸤⟅⦓⦕⸦⸨｟⧘⧚⸜⸌⸂⸄⸉᚛༺༼')
clozbrckt = (')]}）］｝⦆〛⦄”’›»」〉》】〕⦘』〗〙｣⟧⟩⟫⟯⟭⌉⌋⦈⦊❜❞❩❫❵❭❯❱❳'
             '⏝⎵⏟〞︶⏡﹂﹄︺︼︘﹀︾﹈︸〉⦒⧽﹚﹜﹞⁾₎⦌⦎⦐⁆⸣⸥⟆⦔⦖⸧⸩｠⧙⧛⸝⸍⸃⸅⸊᚜༻༽')

ucjk = frozenset(itertools.chain(
    range(0x1100, 0x11FF + 1),
    range(0x2E80, 0xA4CF + 1),
    range(0xA840, 0xA87F + 1),
    range(0xAC00, 0xD7AF + 1),
    range(0xF900, 0xFAFF + 1),
    range(0xFE30, 0xFE4F + 1),
    range(0xFF65, 0xFFDC + 1),
    range(0xFF01, 0xFF0F + 1),
    range(0xFF1A, 0xFF20 + 1),
    range(0xFF3B, 0xFF40 + 1),
    range(0xFF5B, 0xFF60 + 1),
    range(0x20000, 0x2FFFF + 1)
))

zhmodel = None
_curpath = os.path.normpath(
    os.path.join(os.getcwd(), os.path.dirname(__file__)))

RE_WS_IN_FW = re.compile(
    r'([‘’“”…─\u2e80-\u312f\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\ufe30-\ufe57\uff00-\uffef\U00020000-\U0002A6D6])\s+(?=[‘’“”…\u2e80-\u312f\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\ufe30-\ufe57\uff00-\uffef\U00020000-\U0002A6D6])')

RE_FW = re.compile(
    '([\u2018\u2019\u201c\u201d\u2026\u2e80-\u312f\u3200-\u32ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\ufe30-\ufe57\uff00-\uffef\U00020000-\U0002A6D6]+)')

RE_UCJK = re.compile(
    '([\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U0002A6D6]+)')

RE_CTRL = re.compile("[\000-\037\ufeff]+")

hasucjk = lambda s: RE_UCJK.search(s)
removectrl = lambda s: RE_CTRL.sub('', s)

detokenize = lambda s: RE_WS_IN_FW.sub(r'\1', s).strip()
detokenize.__doc__ = 'Detokenization function for Chinese.'

def splitsentence(sentence):
    '''Split a piece of Chinese into sentences.'''
    # s = ''.join((chr(ord(ch)+0xFEE0) if ch in halfwidth else ch) for ch in sentence)
    s = sentence
    slist = []
    for i in resentencesp.split(s):
        if resentencesp.match(i) and slist:
            slist[-1] += i
        elif i:
            slist.append(i)
    return slist


def splithard(sentence, maxchar=None):
    '''Forcely split a piece of Chinese into sentences with the limit of max sentence length.'''
    slist = splitsentence(sentence)
    if maxchar is None:
        return slist
    slist1 = []
    for sent in slist:
        if len(sent) > maxchar:
            for i in resplitpunct.split(sent):
                if resplitpunct.match(i) and slist1:
                    slist1[-1] += i
                elif i:
                    slist1.append(i)
        else:
            slist1.append(sent)
    slist = slist1
    slist1 = []
    for sent in slist:
        if len(sent) > maxchar:
            slist1.extend(sent[i:i + maxchar]
                          for i in range(0, len(sent), maxchar))
        else:
            slist1.append(sent)
    slist = slist1
    return slist


def fixmissing(slist):
    '''Fix missing quotes.'''
    newlist = []
    for i in slist:
        newlist.extend(filter(None, refixmissing.split(i)))
    return newlist


def filterlist(slist):
    '''Get meaningful sentences.'''
    for i in slist:
        s = i.lstrip(tailpunct).rstrip(headpunct)
        if len(s) > 1:
            yield s


def addwalls(tokiter):
    '''Add walls between punctuations for Moses.'''
    lastwall = False
    for tok in tokiter:
        if tok in punct:
            if not lastwall:
                yield '<wall />'
            yield tok
            yield '<wall />'
            lastwall = True
        else:
            yield tok
            lastwall = False


def addwallzone(tokiter):
    '''Add walls and zones between punctuations for Moses.'''
    W = '<wall />'
    out = []
    expect = zidx = None
    for tok in tokiter:
        if tok in punct:
            if not (out and out[-1] == W):
                out.append(W)
            if tok == expect:
                out[zidx] = '<zone>'
                out.append(tok)
                out.append('</zone>')
                expect = zidx = None
            else:
                bid = openbrckt.find(tok)
                if bid > -1:
                    expect = clozbrckt[bid]
                    zidx = len(out) - 1
                out.append(tok)
                out.append(W)
        else:
            out.append(tok)
    if out and out[0] == W:
        out.pop(0)
    if out and out[-1] == W:
        out.pop()
    return out


def calctxtstat(s):
    '''Detect whether a string is modern or classical Chinese.'''
    global zhmodel
    if zhmodel is None:
        import json
        zhmodel = json.load(
            open(os.path.join(_curpath, 'modelzh.json'), 'r', encoding='utf-8'))
    cscore = 0
    mscore = 0
    for ch in s:
        ordch = ord(ch)
        if 0x4E00 <= ordch < 0x9FCD:
            cscore += zhmodel['zhc'][ordch - 0x4E00]
            mscore += zhmodel['zhm'][ordch - 0x4E00]
    return (cscore, mscore)


def checktxttype(cscore, mscore):
    if cscore > mscore:
        return 'c'
    elif cscore < mscore:
        return 'm'
    else:
        return None


def num2chinese(num, big=False, simp=True, o=False, twoalt=False):
    """
    Converts numbers to Chinese representations.

    `big`   : use financial characters.
    `simp`  : use simplified characters instead of traditional characters.
    `o`     : use 〇 for zero.
    `twoalt`: use 两/兩 for two when appropriate.

    Note that `o` and `twoalt` is ignored when `big` is used, 
    and `twoalt` is ignored when `o` is used for formal representations.
    """
    # check num first
    nd = str(num)
    if abs(float(nd)) >= 1e48:
        raise ValueError('number out of range')
    elif 'e' in nd:
        raise ValueError('scientific notation is not supported')
    c_symbol = '正负点' if simp else '正負點'
    if o:  # formal
        twoalt = False
    if big:
        c_basic = '零壹贰叁肆伍陆柒捌玖' if simp else '零壹貳參肆伍陸柒捌玖'
        c_unit1 = '拾佰仟'
        c_twoalt = '贰' if simp else '貳'
    else:
        c_basic = '〇一二三四五六七八九' if o else '零一二三四五六七八九'
        c_unit1 = '十百千'
        if twoalt:
            c_twoalt = '两' if simp else '兩'
        else:
            c_twoalt = '二'
    c_unit2 = '万亿兆京垓秭穰沟涧正载' if simp else '萬億兆京垓秭穰溝澗正載'
    revuniq = lambda l: ''.join(k for k, g in itertools.groupby(reversed(l)))
    nd = str(num)
    result = []
    if nd[0] == '+':
        result.append(c_symbol[0])
    elif nd[0] == '-':
        result.append(c_symbol[1])
    if '.' in nd:
        integer, remainder = nd.lstrip('+-').split('.')
    else:
        integer, remainder = nd.lstrip('+-'), None
    if int(integer):
        splitted = [integer[max(i - 4, 0):i]
                    for i in range(len(integer), 0, -4)]
        intresult = []
        for nu, unit in enumerate(splitted):
            # special cases
            if int(unit) == 0:  # 0000
                intresult.append(c_basic[0])
                continue
            elif nu > 0 and int(unit) == 2:  # 0002
                intresult.append(c_twoalt + c_unit2[nu - 1])
                continue
            ulist = []
            unit = unit.zfill(4)
            for nc, ch in enumerate(reversed(unit)):
                if ch == '0':
                    if ulist:  # ???0
                        ulist.append(c_basic[0])
                elif nc == 0:
                    ulist.append(c_basic[int(ch)])
                elif nc == 1 and ch == '1' and unit[1] == '0':
                    # special case for tens
                    # edit the 'elif' if you don't like
                    # 十四, 三千零十四, 三千三百一十四
                    ulist.append(c_unit1[0])
                elif nc > 1 and ch == '2':
                    ulist.append(c_twoalt + c_unit1[nc - 1])
                else:
                    ulist.append(c_basic[int(ch)] + c_unit1[nc - 1])
            ustr = revuniq(ulist)
            if nu == 0:
                intresult.append(ustr)
            else:
                intresult.append(ustr + c_unit2[nu - 1])
        result.append(revuniq(intresult).strip(c_basic[0]))
    else:
        result.append(c_basic[0])
    if remainder:
        result.append(c_symbol[2])
        result.append(''.join(c_basic[int(ch)] for ch in remainder))
    return ''.join(result)


stripquotes = lambda s: s.lstrip('"‘“「『').rstrip('"’”」』')
fw2hw = lambda s: ''.join(
    (chr(ord(ch) - 0xFEE0) if ord(ch) in fullwidth else ch) for ch in s)
hw2fw = lambda s: ''.join(
    (chr(ord(ch) + 0xFEE0) if ch in halfwidth else ch) for ch in s)


def _test_fixsplit():
    test = """从高祖父到曾孙称为“九族”。这“九族”代表着长幼尊卑秩序和家族血统的承续关系。
《诗》、《书》、《易》、《礼》、《春秋》，再加上《乐》称“六经”，这是中国古代儒家的重要经典，应当仔细阅读。
这就是：宇宙间万事万物循环变化的道理的书籍。
《连山》、《归藏》、《周易》，是我国古代的三部书，这三部书合称“三易”，“三易”是用“卦”的形式来说明宇宙间万事万物循环变化的道理的书籍。
登楼而望，慨然而叹曰：“容容其山，旅旅其石，与地终也!吁嗟人乎!病之蚀气也，如水浸火。
吾闻老聃多寿，尝读其书曰：‘吾惟无身，是以无患。’盖欲窃之而未能也”齐宣王见孟子于雪宫。
“昔者齐景公问于晏子曰：‘吾欲观于转附、朝舞，遵海而南，放于琅邪。吾何修而可以比于先王观也？’
高祖说：“该怎样对付呢？”陈平说：“古代天子有巡察天下，召集诸侯。南方有云梦这个地方，陛下只管假装外出巡游云梦，在陈地召集诸侯。陈地在楚国的西边边境上，韩信听说天子因为爱好外出巡游，看形势必然没有什么大事，就会到国境外来拜见陛下。拜见，陛下趁机抓住他，这只是一个力士的事情而已。”“不知道。”高祖认为有道理。
。他们就是这样的。
""".strip().split('\n')
    for s in test:
        print(fixmissing(splitsentence(s)))

if __name__ == '__main__':
    import sys
    _test_fixsplit()
    print(' '.join(addwallzone('《连山》、《归藏》、《周易》，是我国古代的三部书，这三部书合称“三易”，“三易”是用“卦”的形式来说明(宇宙间万事万物循环变化的道理的书籍。')))
    # print(checktxttype(sys.stdin.read()))
