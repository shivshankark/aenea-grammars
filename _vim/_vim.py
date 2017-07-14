# Dragonfly module for controlling vim on Linux modelessly. All verbal commands
# start and end in command mode, making it effective to combine voice and
# keyboard.
#

LEADER = 'comma'

import aenea.config
import aenea.misc
import aenea.vocabulary

from aenea import (
    Function,
    IntegerRef,
    Key,
    NoAction,
    Text
    )

from aenea.proxy_contexts import ProxyAppContext

from dragonfly import (
    Alternative,
    AppContext,
    CompoundRule,
    Dictation,
    Grammar,
    MappingRule,
    Repetition,
    RuleRef
    )


vim_context = aenea.wrappers.AeneaContext(
    ProxyAppContext(match='regex', title='(?i).*(VIM|FG).*'),
    AppContext(title='VIM')
    )
eclipse_context = aenea.wrappers.AeneaContext(
    ProxyAppContext(match='regex', title='(?i).*ECLIPSE.*'),
    AppContext(title='ECLIPSE')
    )

command_t_context = aenea.wrappers.AeneaContext(
    ProxyAppContext(match='regex', title='^GoToFile.*$'),
    AppContext(title='GoToFile')
    ) & vim_context

fugitive_index_context = aenea.wrappers.AeneaContext(
    ProxyAppContext(match='regex', title='^index.*\.git.*$'),
    AppContext(title='index') & AppContext('.git')
    ) & vim_context

grammar = Grammar('vim', context=vim_context)

from dragonfly import DictListRef

VIM_TAGS = ['vim.insertions.code', 'vim.insertions']
aenea.vocabulary.inhibit_global_dynamic_vocabulary('vim', VIM_TAGS, vim_context)


# TODO: this can NOT be the right way to do this...
class NumericDelegateRule(CompoundRule):
    def value(self, node):
        delegates = node.children[0].children[0].children
        value = delegates[-1].value()
        if delegates[0].value() is not None:
            return Text('%s' % delegates[0].value()) + value
        else:
            return value


class _DigitalIntegerFetcher(object):
    def __init__(self):
        self.cached = {}

    def __getitem__(self, length):
        if length not in self.cached:
            self.cached[length] = aenea.misc.DigitalInteger('count', 1, length)
        return self.cached[length]
ruleDigitalInteger = _DigitalIntegerFetcher()


class LetterMapping(MappingRule):
    mapping = aenea.misc.LETTERS
ruleLetterMapping = RuleRef(LetterMapping(), name='LetterMapping')


def execute_insertion_buffer(insertion_buffer):
    if not insertion_buffer:
        return

    if insertion_buffer[0][0] is not None:
        insertion_buffer[0][0].execute()
    else:
        Key('a').execute()

    for insertion in insertion_buffer:
        insertion[1].execute()

    Key('escape:2').execute()

# ****************************************************************************
# IDENTIFIERS
# ****************************************************************************


class InsertModeEntry(MappingRule):
    mapping = {
        'inns|insert': Key('i'),
        'syn|append': Key('a'),
        'phyllo|insert below': Key('o'),
        'phyhigh|insert above': Key('O'),
        }
ruleInsertModeEntry = RuleRef(InsertModeEntry(), name='InsertModeEntry')


def format_snakeword(text):
    formatted = text[0][0].upper()
    formatted += text[0][1:]
    formatted += ('_' if len(text) > 1 else '')
    formatted += format_score(text[1:])
    return formatted


def format_score(text):
    return '_'.join(text)


def format_camel(text):
    return text[0] + ''.join([word[0].upper() + word[1:] for word in text[1:]])


def format_proper(text):
    return ''.join(word.capitalize() for word in text)


def format_relpath(text):
    return '/'.join(text)


def format_abspath(text):
    return '/' + format_relpath(text)


def format_scoperesolve(text):
    return '::'.join(text)


def format_jumble(text):
    return ''.join(text)


def format_capdotword(text):
    return '.'.join([text[0].capitalize()] + text[1:])

def format_dotword(text):
    return '.'.join(text)


def format_dashword(text):
    return '-'.join(text)


def format_say(text):
    return ' '.join(text)

def format_natword(text):
    return ' '.join(text)


def format_broodingnarrative(text):
    return ''


def format_sentence(text):
    return ' '.join([text[0].capitalize()] + text[1:])


class IdentifierInsertion(CompoundRule):
    spec = ('[upper | natural] ( proper | camel | rel-path | abs-path | score | sentence |'
            'scope-resolve | jumble | dotword | capdotword |  dashword | natword | say | snakeword | brooding-narrative) [<dictation>]')
    extras = [Dictation(name='dictation')]

    def value(self, node):
        words = node.words()

        uppercase = words[0] == 'upper'
        lowercase = words[0] != 'natural'

        if lowercase:
            words = [word.lower() for word in words]
        if uppercase:
            words = [word.upper() for word in words]

        words = [word.split('\\', 1)[0].replace('-', '') for word in words]
        if words[0].lower() in ('upper', 'natural'):
            del words[0]

        function = globals()['format_%s' % words[0].lower()]
        formatted = function(words[1:])

        return Text(formatted)
ruleIdentifierInsertion = RuleRef(
    IdentifierInsertion(),
    name='IdentifierInsertion'
    )


class LiteralIdentifierInsertion(CompoundRule):
    spec = '[<InsertModeEntry>] literal <IdentifierInsertion>'
    extras = [ruleIdentifierInsertion, ruleInsertModeEntry]

    def value(self, node):
        children = node.children[0].children[0].children
        return [('i', (children[0].value(), children[2].value()))]
ruleLiteralIdentifierInsertion = RuleRef(
    LiteralIdentifierInsertion(),
    name='LiteralIdentifierInsertion'
    )


# ****************************************************************************
# INSERTIONS
# ****************************************************************************

class KeyInsertion(MappingRule):
    mapping = {
        'ace [<count>]':        Key('space:%(count)d'),
        'tab [<count>]':        Key('tab:%(count)d'),
        'slap [<count>]':       Key('enter:%(count)d'),
        'chuck [<count>]':      Key('del:%(count)d'),
        'scratch [<count>]':    Key('backspace:%(count)d'),
        'ack|act':              Key('escape'),
        }
    extras = [ruleDigitalInteger[3]]
    defaults = {'count': 1}
ruleKeyInsertion = RuleRef(KeyInsertion(), name='KeyInsertion')


class SpellingInsertion(MappingRule):
    mapping = dict(('dig|digit ' + key, val) for (key, val) in aenea.misc.DIGITS.iteritems())
    mapping.update(aenea.misc.LETTERS)

    def value(self, node):
        return Text(MappingRule.value(self, node))
ruleSpellingInsertion = RuleRef(SpellingInsertion(), name='SpellingInsertion')


class ArithmeticInsertion(MappingRule):
    mapping = {
        'assign':           Text('= '),
        'compare eek':      Text('== '),
        'compare not eek':  Text('!= '),
        'compare greater':  Text('> '),
        'compare less':     Text('< '),
        'compare geck':     Text('>= '),
        'compare lack':     Text('<= '),
        'bit ore':          Text('| '),
        'bit and':          Text('& '),
        'bit ex or':        Text('^ '),
        'times':            Text('* '),
        'divided':          Text('/ '),
        'plus':             Text('+ '),
        'minus':            Text('- '),
        'plus equal':       Text('+= '),
        'minus equal':      Text('-= '),
        'times equal':      Text('*= '),
        'divided equal':    Text('/= '),
        'mod equal':        Text('%%= '),
        }
ruleArithmeticInsertion = RuleRef(
    ArithmeticInsertion(),
    name='ArithmeticInsertion'
    )


primitive_insertions = [
    ruleKeyInsertion,
    ruleIdentifierInsertion,
    DictListRef(
        'dynamic vim.insertions.code',
        aenea.vocabulary.register_dynamic_vocabulary('vim.insertions.code')
        ),
    DictListRef(
        'dynamic vim.insertions',
        aenea.vocabulary.register_dynamic_vocabulary('vim.insertions')
        ),
    ruleArithmeticInsertion,
    ruleSpellingInsertion,
    ]


static_code_insertions = aenea.vocabulary.get_static_vocabulary('vim.insertions.code')
static_insertions = aenea.vocabulary.get_static_vocabulary('vim.insertions')

if static_code_insertions:
    primitive_insertions.append(
        RuleRef(
            MappingRule(
                'static vim.insertions,code mapping',
                mapping=aenea.vocabulary.get_static_vocabulary('vim.insertions.code')
                ),
            'static vim.insertions.code'
            )
        )

if static_insertions:
    primitive_insertions.append(
        RuleRef(
            MappingRule(
                'static vim.insertions mapping',
                mapping=aenea.vocabulary.get_static_vocabulary('vim.insertions')
                ),
            'static vim.insertions'
            )
        )


class PrimitiveInsertion(CompoundRule):
    spec = '<insertion>'
    extras = [Alternative(primitive_insertions, name='insertion')]

    def value(self, node):
        children = node.children[0].children[0].children
        return children[0].value()
rulePrimitiveInsertion = RuleRef(
    PrimitiveInsertion(),
    name='PrimitiveInsertion'
    )


class PrimitiveInsertionRepetition(CompoundRule):
    spec = '<PrimitiveInsertion> [ parrot <count> ]'
    extras = [rulePrimitiveInsertion, ruleDigitalInteger[3]]

    def value(self, node):
        children = node.children[0].children[0].children
        holder = children[1].value()[1] if children[1].value() else 1
        value = children[0].value() * holder
        return value
rulePrimitiveInsertionRepetition = RuleRef(
    PrimitiveInsertionRepetition(),
    name='PrimitiveInsertionRepetition'
    )


class Insertion(CompoundRule):
    spec = '[<InsertModeEntry>] <PrimitiveInsertionRepetition>'
    extras = [rulePrimitiveInsertionRepetition, ruleInsertModeEntry]

    def value(self, node):
        children = node.children[0].children[0].children
        return [('i', (children[0].value(), children[1].value()))]
ruleInsertion = RuleRef(Insertion(), name='Insertion')


# ****************************************************************************
# MOTIONS
# ****************************************************************************


class PrimitiveMotion(MappingRule):
    mapping = {
        'up': Text('k'),
        'down': Text('j'),
        'left': Text('h'),
        'right': Text('l'),

        'lope': Text('b'),
        'yope': Text('w'),
        'elope': Text('ge'),
        'iyope': Text('e'),

        'lopert': Text('B'),
        'yopert': Text('W'),
        'elopert': Text('gE'),
        'eyopert': Text('E'),

        'apla': Text('{'),
        'anla': Text('}'),
        'sapla': Text('('),
        'sanla': Text(')'),

        'care': Text('^'),
        'hard care': Text('0'),
        'doll': Text('$'),

        'screecare': Text('g^'),
        'screedoll': Text('g$'),

        'scree up': Text('gk'),
        'scree down': Text('gj'),

        'wynac': Text('G'),

        'wynac top': Text('H'),
        'wynac toe': Text('L'),

        # CamelCaseMotion plugin
        'calalope': Text(',b'),
        'calayope': Text(',w'),
        'end calayope': Text(',e'),
        'inner calalope': Text('i,b'),
        'inner calayope': Text('i,w'),
        'inner end calayope': Text('i,e'),

        # EasyMotion
        'easy lope': Key('%s:2, b' % LEADER),
        'easy yope': Key('%s:2, w' % LEADER),
        'easy elope': Key('%s:2, g, e' % LEADER),
        'easy iyope': Key('%s:2, e' % LEADER),

        'easy lopert': Key('%s:2, B' % LEADER),
        'easy yopert': Key('%s:2, W' % LEADER),
        'easy elopert': Key('%s:2, g, E' % LEADER),
        'easy eyopert': Key('%s:2, E' % LEADER),
        }

    for (spoken_object, command_object) in (('(lope | yope)', 'w'),
                                            ('(lopert | yopert)', 'W'),
                                            ('smote',"'"),
                                            ('quote','"'),
                                            ('circle','('),
                                            ('square','['),
                                            ('box','{')
                                            ):
        for (spoken_modifier, command_modifier) in (('inner', 'i'),
                                                    ('around', 'a'),
                                                    ('outer', 'a'),
                                                    ('phytic', 'f'),
                                                    ('fitton', 't')):
            map_action = Text(command_modifier + command_object)
            mapping['%s %s' % (spoken_modifier, spoken_object)] = map_action
rulePrimitiveMotion = RuleRef(PrimitiveMotion(), name='PrimitiveMotion')


class UncountedMotion(MappingRule):
    mapping = {
        'matching': Text('%%'),
        'matu': Text('M'),
        }
ruleUncountedMotion = RuleRef(UncountedMotion(), name='UncountedMotion')


class MotionParameterMotion(MappingRule):
    mapping = {
        'phytic': 'f',
        'pre phytic': 'F',
        'fitton': 't',
        'pre fitton': 'T',
        }
ruleMotionParameterMotion = RuleRef(
    MotionParameterMotion(),
    name='MotionParameterMotion'
    )


class ParameterizedMotion(CompoundRule):
    spec = '<MotionParameterMotion> <LetterMapping>'
    extras = [ruleLetterMapping, ruleMotionParameterMotion]

    def value(self, node):
        children = node.children[0].children[0].children
        return Text(children[0].value() + children[1].value())
ruleParameterizedMotion = RuleRef(
    ParameterizedMotion(),
    name='ParameterizedMotion'
    )


class CountedMotion(NumericDelegateRule):
    spec = '[<count>] <motion>'
    extras = [ruleDigitalInteger[3],
              Alternative([
                  rulePrimitiveMotion,
                  ruleParameterizedMotion], name='motion')]
ruleCountedMotion = RuleRef(CountedMotion(), name='CountedMotion')


class Motion(CompoundRule):
    spec = '<motion>'
    extras = [Alternative(
        [ruleCountedMotion, ruleUncountedMotion],
        name='motion'
        )]

    def value(self, node):
        return node.children[0].children[0].children[0].value()

ruleMotion = RuleRef(Motion(), name='Motion')


# ****************************************************************************
# OPERATORS
# ****************************************************************************

_OPERATORS = {
    'relo': '',
    'dale|dell': 'd',
    'chaos': 'c',
    'nab': 'y',
    'swap case': 'g~',
    'uppercase': 'gU',
    'lowercase': 'gu',
    'external filter': '!',
    'external format': '=',
    'format text': 'gq',
    'rotate thirteen': 'g?',
    'indent left': '<',
    'indent right': '>',
    'define fold': 'zf',
    }


class PrimitiveOperator(MappingRule):
    mapping = dict((key, Text(val)) for (key, val) in _OPERATORS.iteritems())
    # tComment
    mapping['comm nop'] = Text('gc')
rulePrimitiveOperator = RuleRef(PrimitiveOperator(), name='PrimitiveOperator')


class Operator(NumericDelegateRule):
    spec = '[<count>] <PrimitiveOperator>'
    extras = [ruleDigitalInteger[3],
              rulePrimitiveOperator]
ruleOperator = RuleRef(Operator(), name='Operator')


class OperatorApplicationMotion(CompoundRule):
    spec = '[<Operator>] <Motion>'
    extras = [ruleOperator, ruleMotion]

    def value(self, node):
        children = node.children[0].children[0].children
        return_value = children[1].value()
        if children[0].value() is not None:
            return_value = children[0].value() + return_value
        return return_value
ruleOperatorApplicationMotion = RuleRef(
    OperatorApplicationMotion(),
    name='OperatorApplicationMotion'
    )


class OperatorSelfApplication(MappingRule):
    mapping = dict(('%s [<count>] %s' % (key, key), Text('%s%%(count)d%s' % (value, value)))
                   for (key, value) in _OPERATORS.iteritems())
    # tComment
    # string not action intentional dirty hack.
    mapping['comm nop [<count>] comm nop'] = 'tcomment'
    extras = [ruleDigitalInteger[3]]
    defaults = {'count': 1}

    def value(self, node):
        value = MappingRule.value(self, node)
        if value == 'tcomment':
            # ugly hack to get around tComment's not allowing ranges with gcc.
            value = node.children[0].children[0].children[0].children[1].value()
            if value in (1, '1', None):
                return Text('gcc')
            else:
                return Text('gc%dj' % (int(value) - 1))
        else:
            return value

ruleOperatorSelfApplication = RuleRef(
    OperatorSelfApplication(),
    name='OperatorSelfApplication'
    )

ruleOperatorApplication = Alternative([ruleOperatorApplicationMotion,
                                       ruleOperatorSelfApplication],
                                      name='OperatorApplication')


# ****************************************************************************
# COMMANDS
# ****************************************************************************

def goto_line(n):
    for c in str(n):
        Key(c).execute()
    Key("G").execute()


def yank_lines(n, n2):
    goto_line(n)
    Key("V").execute()
    goto_line(n2)
    Key("y").execute()


def delete_lines(n, n2):
    goto_line(n)
    Key("V").execute()
    goto_line(n2)
    Key("d").execute()


basics_mapping = aenea.configuration.make_grammar_commands('vim', {
    'vim': Text("vim"),

#    # Moving between splits
#    'split-left': Key("escape, c-h"),
#    'split-left <n>': Key("escape, c-h:%(n)d"),
#    'split-right': Key("escape, c-l"),
#    'split-right <n>': Key("escape, c-l:%(n)d"),
#    'split-up': Key("escape, c-k"),
#    'split-down': Key("escape, c-j"),
#    'split-close': Key("escape, colon, q, enter"),
#    'open [in] split': Key("s"),
#    'open [in] tab': Key("t"),

    # Moving viewport
    'set number': Key("escape") + Text(":set number") + Key("enter"),
#    'bund': Key("escape, 2, 0, c-y"),
#    'fund': Key("escape, 2, 0, c-e"),
    'screen down': Key("escape, c-f"),
    'screen up': Key("escape, c-b"),
    'screen center': Key("escape, z") + Text("."),
    'screen top': Key("escape, z, t"),
    'screen bottom': Key("escape, z, b"),

#    # Append to line
#    'noop <n>': Key("escape") + Function(goto_line) + Key("A, enter"),
#    'noop': Key("escape, A, enter"),
#    'nope': Key("escape, A"),
#    'nope <n>': Key("escape") + Function(goto_line) + Key("A"),
#
#    'prepend': Key("escape, I"),
#    'insert': Key("escape, i"),
#    'insert below': Key("escape, o"),
#    'insert above': Key("escape, O"),
#    'undo': Key("escape, u, i"),
#    'scratch': Key("escape, u, i"),
#    'escape': Key("escape"),
    'filename': Key("escape, c-g"),
    'save [file]': Key("escape, colon, w, enter"),
    'save and quit': Key("escape, colon, w, q, enter"),
    'quit all': Key("escape, colon, q, a, enter"),
    'discard': Key("escape, colon, q, exclamation"),
#    '(vim|vic) tab <n>': Key("escape, comma, %(n)d"),
#    'comma': Key("comma"),
#    'comes': Key("comma, space"),
#    'bish': Key("right, comma, space"),
#    'cause': Key("colon, space"),
#    '(rook|Brook|rock)': Key("right, colon, space"),
#    'listed': Key("escape, s-a, comma, enter"),
#    'fish': Key("right, rparen"),

    # Finding text
    #'find <text>': Key("escape, slash") + Text("%(text)s") + Key("enter"),
    'next': Key("escape, n"),
    'prev|previous': Key("escape, N"),
    'clear search': Key("escape, colon, n, o, h, enter"),

#    # Character operations
    'dart': Key("x"),
    'dart <n>': Key("x:%(n)d"),
    'replace letter': Key("r"),
    'replace mode': Key("R"),
    'change case': Key("s-backtick"),
    'change case back': Key("b, s-backtick"),

#    # Word operations
#    '(doord|doored|gord)': Key("right, escape, d, i, w, i"),
#    '(doord|doored|gord) back': Key("right, escape, b, d, w, i"),
#    '(doord|doored|gord) <n>': Key("right, escape, %(n)d, d, w, i"),
#    '(doord|doored|gord) back <n>': Key("right, escape, %(n)d, b, %(n)d, d, w, i"),
#    'chord': Key("right, escape, c, i, w"),
#    'chord <n>': Key("escape, right, c, %(n)d, w"),
#    'sword': Key("escape, right, v, e"),
#    'sword <n>': Key("escape, right, v, e:%(n)d"),
#    'forward':  Key("escape, right, w, i"),
#    'forward <n>': Key("escape, right, %(n)d, w, i"),
#    'backward': Key("escape, b, i"),
#    'backward <n>': Key("escape, %(n)d, b, i"),
#    'stripword': Key("escape, b, left, del, e, a"),
#
#    # Line operations
#    'dine': Key("escape, d:2"),
#    'dine <n>': Key("escape") + Function(goto_line) + Key("d:2"),
#    'dine paragraph' : Key("escape") + Key("d,a,p"), 
#    'dine <n> (thru|through|to) <n2>': Key("escape") + Function(delete_lines),
#    'chin': Key("escape, c:2"),
#    'chin <n>': Key("escape") + Function(goto_line) + Key("c:2"),
#    'nab line': Key("escape, y:2"),
#    'nab line <n>': Key("escape") + Function(goto_line) + Key("y:2"),
#    'nab line <n> (thru|through|to) <n2>': Key("escape") + Function(yank_lines),
#
#    'select until <pressKey>': Key("escape, v, t") + Text("%(pressKey)s"),
#    'select including <pressKey>': Key("escape, v, f") + Text("%(pressKey)s"),
#    'dell until <pressKey>': Key("escape, d, t") + Text("%(pressKey)s"),
#    'dell including <pressKey>': Key("escape, d, f") + Text("%(pressKey)s"),
#
#    # Fancy operations
#    'clay': Key("escape, c, i, dqoute"),
#    'yip': Key("escape, right, y, i, lparen"),
#    'yib': Key("escape, right, y, i lbrace"),
#    'dap': Key("escape, right, s-d, s-a"),
#
#    # Copy and Paste
#    'yank': Key("y"),
#    'extract': Key("x"),
#    'glue': Key('escape, p'),
#
    # Movement
#    'up <n> (lines|line)': Key("%(n)d, up"),
#    'down <n> (lines|line)': Key("%(n)d, down"),
    'go to [line] <n>': Key("escape") + Function(goto_line),
#    'matching': Key("escape, percent"),
#    'rash': Key("escape, down, s-a"),
#    'back': Key("escape, c-o"),
#
#    # Plug-ins
#    'curb': Key("c-p"),
#    'curb tab': Key("c-t"),
#    'curb split': Key("c-v"),
#    'nerd': Key("escape, colon") + Text("NERDTreeToggle") + Key("enter"),
    })


class Basics(MappingRule):
    mapping = basics_mapping
    extras = [
        Dictation('text'),
        IntegerRef('n', 1, 999),
        IntegerRef('n2', 1, 999),
#        Choice("pressKey", pressKeyMap),
#        Choice("surroundChar", surroundCharsMap),
    ]


class PrimitiveCommand(MappingRule):
    mapping = {
        'vim scratch': Key('X'),
        'vim chuck': Key('x'),
        'undo': Key('u'),
        'plap': Key('P'),
        'plop': Key('p'),
        'ditto|repeat': Text('.'),
        'ripple': 'macro',
        }
rulePrimitiveCommand = RuleRef(PrimitiveCommand(), name='PrimitiveCommand')


class Command(CompoundRule):
    spec = '[<count>] [reg <LetterMapping>] <command>'
    extras = [Alternative([ruleOperatorApplication,
                           rulePrimitiveCommand,
                           ], name='command'),
              ruleDigitalInteger[3],
              ruleLetterMapping]

    def value(self, node):
        delegates = node.children[0].children[0].children
        value = delegates[-1].value()
        prefix = ''
        if delegates[0].value() is not None:
            prefix += str(delegates[0].value())
        if delegates[1].value() is not None:
            # Hack for macros
            reg = delegates[1].value()[1]
            if value == 'macro':
                prefix += '@' + reg
                value = None
            else:
                prefix += "'" + reg
        if prefix:
            if value is not None:
                value = Text(prefix) + value
            else:
                value = Text(prefix)
        # TODO: ugly hack; should fix the grammar or generalize.
        if 'chaos' in zip(*node.results)[0]:
            return [('c', value), ('i', (NoAction(),) * 2)]
        else:
            return [('c', value)]
ruleCommand = RuleRef(Command(), name='Command')


# ****************************************************************************


class VimCommand(CompoundRule):
    spec = ('[<app>] [<literal>]')
    extras = [Repetition(Alternative([ruleCommand, RuleRef(Insertion())]), max=10, name='app'),
              RuleRef(LiteralIdentifierInsertion(), name='literal')]

    def _process_recognition(self, node, extras):
        insertion_buffer = []
        commands = []
        if 'app' in extras:
            for chunk in extras['app']:
                commands.extend(chunk)
        if 'literal' in extras:
            commands.extend(extras['literal'])
        for command in commands:
            mode, command = command
            if mode == 'i':
                insertion_buffer.append(command)
            else:
                execute_insertion_buffer(insertion_buffer)
                insertion_buffer = []
                command.execute(extras)
        execute_insertion_buffer(insertion_buffer)

grammar.add_rule(VimCommand())
grammar.add_rule(Basics())

grammar.load()


def unload():
    aenea.vocabulary.uninhibit_global_dynamic_vocabulary('vim', VIM_TAGS)
    for tag in VIM_TAGS:
        aenea.vocabulary.unregister_dynamic_vocabulary(tag)
    global grammar
    if grammar:
        grammar.unload()
    grammar = None
