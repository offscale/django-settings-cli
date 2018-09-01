from __future__ import generators
import inspect
import sys
import tokenize

from platform import python_version_tuple
from sys import version_info

if python_version_tuple()[0] == '3':
    basestring = str


    def _totext(obj, encoding=None, errors=None):
        if isinstance(obj, bytes):
            if errors is None:
                obj = obj.decode(encoding)
            else:
                obj = obj.decode(encoding, errors)
        elif not isinstance(obj, str):
            obj = str(obj)
        return obj


class Source(object):
    """ a immutable object holding a source code fragment,
        possibly deindenting it.
    """
    _compilecounter = 0

    def __init__(self, *parts, **kwargs):
        self.lines = lines = []
        de = kwargs.get('deindent', True)
        rstrip = kwargs.get('rstrip', True)
        for part in parts:
            if not part:
                partlines = []
            if isinstance(part, Source):
                partlines = part.lines
            elif isinstance(part, (tuple, list)):
                partlines = [x.rstrip("\n") for x in part]
            elif isinstance(part, basestring):
                partlines = part.split('\n')
                if rstrip:
                    while partlines:
                        if partlines[-1].strip():
                            break
                        partlines.pop()
            else:
                partlines = getsource(part, deindent=de).lines
            if de:
                partlines = deindent(partlines)
            lines.extend(partlines)

    def __eq__(self, other):
        try:
            return self.lines == other.lines
        except AttributeError:
            if isinstance(other, str):
                return str(self) == other
            return False

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.lines[key]
        else:
            if key.step not in (None, 1):
                raise IndexError("cannot slice a Source with a step")
            return self.__getslice__(key.start, key.stop)

    def __len__(self):
        return len(self.lines)

    def __getslice__(self, start, end):
        newsource = Source()
        newsource.lines = self.lines[start:end]
        return newsource

    def strip(self):
        """ return new source object with trailing
            and leading blank lines removed.
        """
        start, end = 0, len(self)
        while start < end and not self.lines[start].strip():
            start += 1
        while end > start and not self.lines[end - 1].strip():
            end -= 1
        source = Source()
        source.lines[:] = self.lines[start:end]
        return source

    def putaround(self, before='', after='', indent=' ' * 4):
        """ return a copy of the source object with
            'before' and 'after' wrapped around it.
        """
        before = Source(before)
        after = Source(after)
        newsource = Source()
        lines = [(indent + line) for line in self.lines]
        newsource.lines = before.lines + lines + after.lines
        return newsource

    def indent(self, indent=' ' * 4):
        """ return a copy of the source object with
            all lines indented by the given indent-string.
        """
        newsource = Source()
        newsource.lines = [(indent + line) for line in self.lines]
        return newsource

    def getstatement(self, lineno, assertion=False):
        """ return Source statement which contains the
            given linenumber (counted from 0).
        """
        start, end = self.getstatementrange(lineno, assertion)
        return self[start:end]

    def getstatementrange(self, lineno, assertion=False):
        """ return (start, end) tuple which spans the minimal
            statement region which containing the given lineno.
        """
        if not (0 <= lineno < len(self)):
            raise IndexError("lineno out of range")
        ast, start, end = getstatementrange_ast(lineno, self)
        return start, end

    def deindent(self, offset=None):
        """ return a new source object deindented by offset.
            If offset is None then guess an indentation offset from
            the first non-blank line.  Subsequent lines which have a
            lower indentation offset will be copied verbatim as
            they are assumed to be part of multilines.
        """
        # XXX maybe use the tokenizer to properly handle multiline
        #     strings etc.pp?
        newsource = Source()
        newsource.lines[:] = deindent(self.lines, offset)
        return newsource

    def isparseable(self, deindent=True):
        """ return True if source is parseable, heuristically
            deindenting it by default.
        """
        try:
            import parser
        except ImportError:
            syntax_checker = lambda x: compile(x, 'asd', 'exec')
        else:
            syntax_checker = parser.suite

        if deindent:
            source = str(self.deindent())
        else:
            source = str(self)
        try:
            # compile(source+'\n', "x", "exec")
            syntax_checker(source + '\n')
        except KeyboardInterrupt:
            raise
        except Exception:
            return False
        else:
            return True

    def __str__(self):
        return "\n".join(self.lines)

    '''def compile(self, filename=None, mode='exec',
                flag=generators.compiler_flag,
                dont_inherit=0, _genframe=None):
        """ return compiled code object. if filename is None
            invent an artificial filename which displays
            the source/line position of the caller frame.
        """
        if not filename or py.path.local(filename).check(file=0):
            if _genframe is None:
                _genframe = sys._getframe(1)  # the caller
            fn, lineno = _genframe.f_code.co_filename, _genframe.f_lineno
            base = "<%d-codegen " % self._compilecounter
            self.__class__._compilecounter += 1
            if not filename:
                filename = base + '%s:%d>' % (fn, lineno)
            else:
                filename = base + '%r %s:%d>' % (filename, fn, lineno)
        source = "\n".join(self.lines) + '\n'
        try:
            co = cpy_compile(source, filename, mode, flag)
        except SyntaxError:
            ex = sys.exc_info()[1]
            # re-represent syntax errors from parsing python strings
            msglines = self.lines[:ex.lineno]
            if ex.offset:
                msglines.append(" " * ex.offset + '^')
            msglines.append("(code was compiled probably from here: %s)" % filename)
            newex = SyntaxError('\n'.join(msglines))
            newex.offset = ex.offset
            newex.lineno = ex.lineno
            newex.text = ex.text
            raise newex
        else:
            if flag & _AST_FLAG:
                return co
            lines = [(x + "\n") for x in self.lines]
            if sys.version_info[0] >= 3:
                # XXX py3's inspect.getsourcefile() checks for a module
                # and a pep302 __loader__ ... we don't have a module
                # at code compile-time so we need to fake it here
                m = ModuleType("_pycodecompile_pseudo_module")
                py.std.inspect.modulesbyfile[filename] = None
                py.std.sys.modules[None] = m
                m.__loader__ = 1
            py.std.linecache.cache[filename] = (1, None, lines, filename)
            return co'''


class Frame(object):
    """Wrapper around a Python frame holding f_locals and f_globals
    in which expressions can be evaluated."""

    def __init__(self, frame):
        self.lineno = frame.f_lineno - 1
        self.f_globals = frame.f_globals
        self.f_locals = frame.f_locals
        self.raw = frame
        self.code = Code(frame.f_code)

    @property
    def statement(self):
        """ statement this frame is at """
        if self.code.fullsource is None:
            return py.code.Source("")
        return self.code.fullsource.getstatement(self.lineno)

    def eval(self, code, **vars):
        """ evaluate 'code' in the frame

            'vars' are optional additional local variables

            returns the result of the evaluation
        """
        f_locals = self.f_locals.copy()
        f_locals.update(vars)
        return eval(code, self.f_globals, f_locals)

    def exec_(self, code, **vars):
        """ exec 'code' in the frame

            'vars' are optiona; additional local variables
        """
        f_locals = self.f_locals.copy()
        f_locals.update(vars)
        py.builtin.exec_(code, self.f_globals, f_locals)

    def repr(self, object):
        """ return a 'safe' (non-recursive, one-line) string repr for 'object'
        """
        return saferepr(object)

    def is_true(self, object):
        return object

    def getargs(self, var=False):
        """ return a list of tuples (name, value) for all arguments

            if 'var' is set True also include the variable and keyword
            arguments when present
        """
        retval = []
        for arg in self.code.getargs(var):
            try:
                retval.append((arg, self.f_locals[arg]))
            except KeyError:
                pass  # this can occur when using Psyco
        return retval
class Code(object):
    """ wrapper around Python code objects """
    def __init__(self, rawcode):
        if not hasattr(rawcode, "co_filename"):
            rawcode = getrawcode(rawcode)
        try:
            self.filename = rawcode.co_filename
            self.firstlineno = rawcode.co_firstlineno - 1
            self.name = rawcode.co_name
        except AttributeError:
            raise TypeError("not a code object: %r" %(rawcode,))
        self.raw = rawcode

    def __eq__(self, other):
        return self.raw == other.raw

    def __ne__(self, other):
        return not self == other

    @property
    def path(self):
        """ return a path object pointing to source code (note that it
        might not point to an actually existing file). """
        p = self.raw.co_filename # py.path.local(self.raw.co_filename)
        # maybe don't try this checking
        if not p.check():
            # XXX maybe try harder like the weird logic
            # in the standard lib [linecache.updatecache] does?
            p = self.raw.co_filename
        return p

    @property
    def fullsource(self):
        """ return a py.code.Source object for the full source file of the code
        """
        full, _ = findsource(self.raw)
        return full

    def source(self):
        """ return a py.code.Source object for the code object's source only
        """
        # return source only for that part of code
        return py.code.Source(self.raw)

    def getargs(self, var=False):
        """ return a tuple with the argument names for the code object

            if 'var' is set True also return the names of the variable and
            keyword arguments when present
        """
        # handfull shortcut for getting args
        raw = self.raw
        argcount = raw.co_argcount
        if var:
            argcount += raw.co_flags & CO_VARARGS
            argcount += raw.co_flags & CO_VARKEYWORDS
        return raw.co_varnames[:argcount]

class Repr(object):
    """ An instance of Repr is associated with each instance of SomeXxx.
    It defines the chosen representation for the SomeXxx.  The Repr subclasses
    generally follows the SomeXxx subclass hierarchy, but there are numerous
    exceptions.  For example, the annotator uses SomeIter for any iterator, but
    we need different representations according to the type of container we are
    iterating over.
    """
    __metaclass__ = extendabletype
    _initialized = setupstate.NOTINITIALIZED
    __NOT_RPYTHON__ = True

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, self.lowleveltype)

    def compact_repr(self):
        return '%s %s' % (self.__class__.__name__.replace('Repr', 'R'), self.lowleveltype._short_name())

    def setup(self):
        """ call _setup_repr() and keep track of the initializiation
            status to e.g. detect recursive _setup_repr invocations.
            the '_initialized' attr has four states:
        """
        if self._initialized == setupstate.FINISHED:
            return
        elif self._initialized == setupstate.BROKEN:
            raise BrokenReprTyperError(
                "cannot setup already failed Repr: %r" % (self,))
        elif self._initialized == setupstate.INPROGRESS:
            raise AssertionError(
                "recursive invocation of Repr setup(): %r" % (self,))
        elif self._initialized == setupstate.DELAYED:
            raise AssertionError(
                "Repr setup() is delayed and cannot be called yet: %r" % (self,))
        assert self._initialized == setupstate.NOTINITIALIZED
        self._initialized = setupstate.INPROGRESS
        try:
            self._setup_repr()
        except TyperError:
            self._initialized = setupstate.BROKEN
            raise
        else:
            self._initialized = setupstate.FINISHED

    def _setup_repr(self):
        "For recursive data structure, which must be initialized in two steps."

    def setup_final(self):
        """Same as setup(), called a bit later, for effects that are only
        needed after the typer finished (as opposed to needed for other parts
        of the typer itself)."""
        if self._initialized == setupstate.BROKEN:
            raise BrokenReprTyperError("cannot perform setup_final_touch "
                                       "on failed Repr: %r" % (self,))
        assert self._initialized == setupstate.FINISHED, (
            "setup_final() on repr with state %s: %r" %
            (self._initialized, self))
        self._setup_repr_final()

    def _setup_repr_final(self):
        pass

    def is_setup_delayed(self):
        return self._initialized == setupstate.DELAYED

    def set_setup_delayed(self, flag):
        assert self._initialized in (setupstate.NOTINITIALIZED,
                                     setupstate.DELAYED)
        if flag:
            self._initialized = setupstate.DELAYED
        else:
            self._initialized = setupstate.NOTINITIALIZED

    def set_setup_maybe_delayed(self):
        if self._initialized == setupstate.NOTINITIALIZED:
            self._initialized = setupstate.DELAYED
        return self._initialized == setupstate.DELAYED

    def __getattr__(self, name):
        # Assume that when an attribute is missing, it's because setup() needs
        # to be called
        if not (name[:2] == '__' == name[-2:]):
            if self._initialized == setupstate.NOTINITIALIZED:
                self.setup()
                try:
                    return self.__dict__[name]
                except KeyError:
                    pass
        raise AttributeError("%s instance has no attribute %s" % (
            self.__class__.__name__, name))

    def _freeze_(self):
        return True

    def convert_desc_or_const(self, desc_or_const):
        if isinstance(desc_or_const, description.Desc):
            return self.convert_desc(desc_or_const)
        elif isinstance(desc_or_const, Constant):
            return self.convert_const(desc_or_const.value)
        else:
            raise TyperError("convert_desc_or_const expects a Desc"
                             "or Constant: %r" % desc_or_const)

    def convert_const(self, value):
        "Convert the given constant value to the low-level repr of 'self'."
        if not self.lowleveltype._contains_value(value):
            raise TyperError("convert_const(self = %r, value = %r)" % (
                self, value))
        return value

    def special_uninitialized_value(self):
        return None

    def get_ll_eq_function(self):
        """Return an eq(x,y) function to use to compare two low-level
        values of this Repr.
        This can return None to mean that simply using '==' is fine.
        """
        raise TyperError('no equality function for %r' % self)

    def get_ll_hash_function(self):
        """Return a hash(x) function for low-level values of this Repr.
        """
        raise TyperError('no hashing function for %r' % self)

    def get_ll_fasthash_function(self):
        """Return a 'fast' hash(x) function for low-level values of this
        Repr.  The function can assume that 'x' is already stored as a
        key in a dict.  get_ll_fasthash_function() should return None if
        the hash should rather be cached in the dict entry.
        """
        return None

    def can_ll_be_null(self, s_value):
        """Check if the low-level repr can take the value 0/NULL.
        The annotation s_value is provided as a hint because it may
        contain more information than the Repr.
        """
        return True  # conservative

    def get_ll_dummyval_obj(self, rtyper, s_value):
        """A dummy value is a special low-level value, not otherwise
        used.  It should not be the NULL value even if it is special.
        This returns either None, or a hashable object that has a
        (possibly lazy) attribute 'll_dummy_value'.
        The annotation s_value is provided as a hint because it may
        contain more information than the Repr.
        """
        T = self.lowleveltype
        if (isinstance(T, lltype.Ptr) and
            isinstance(T.TO, (lltype.Struct,
                              lltype.Array,
                              lltype.ForwardReference))):
            return DummyValueBuilder(rtyper, T.TO)
        else:
            return None

    def rtype_bltn_list(self, hop):
        raise TyperError('no list() support for %r' % self)

    def rtype_unichr(self, hop):
        raise TyperError('no unichr() support for %r' % self)

    # default implementation of some operations

    def rtype_getattr(self, hop):
        s_attr = hop.args_s[1]
        if s_attr.is_constant() and isinstance(s_attr.const, str):
            attr = s_attr.const
            s_obj = hop.args_s[0]
            if s_obj.find_method(attr) is None:
                raise TyperError("no method %s on %r" % (attr, s_obj))
            else:
                # implement methods (of a known name) as just their 'self'
                return hop.inputarg(self, arg=0)
        else:
            raise TyperError("getattr() with a non-constant attribute name")

    def rtype_str(self, hop):
        [v_self] = hop.inputargs(self)
        return hop.gendirectcall(self.ll_str, v_self)

    def rtype_bool(self, hop):
        try:
            vlen = self.rtype_len(hop)
        except MissingRTypeOperation:
            if not hop.s_result.is_constant():
                raise TyperError("rtype_bool(%r) not implemented" % (self,))
            return hop.inputconst(Bool, hop.s_result.const)
        else:
            return hop.genop('int_is_true', [vlen], resulttype=Bool)

    def rtype_isinstance(self, hop):
        hop.exception_cannot_occur()
        if hop.s_result.is_constant():
            return hop.inputconst(lltype.Bool, hop.s_result.const)

        if hop.args_s[1].is_constant() and hop.args_s[1].const in (str, list, unicode):
            if hop.args_s[0].knowntype not in (str, list, unicode):
                raise TyperError("isinstance(x, str/list/unicode) expects x to be known"
                                 " statically to be a str/list/unicode or None")
            rstrlist = hop.args_r[0]
            vstrlist = hop.inputarg(rstrlist, arg=0)
            cnone = hop.inputconst(rstrlist, None)
            return hop.genop('ptr_ne', [vstrlist, cnone], resulttype=lltype.Bool)
        raise TyperError

    def rtype_hash(self, hop):
        ll_hash = self.get_ll_hash_function()
        v, = hop.inputargs(self)
        return hop.gendirectcall(ll_hash, v)

    def rtype_iter(self, hop):
        r_iter = self.make_iterator_repr()
        return r_iter.newiter(hop)

    def make_iterator_repr(self, *variant):
        raise TyperError("%s is not iterable" % (self,))

    def rtype_hint(self, hop):
        return hop.inputarg(hop.r_result, arg=0)

    # hlinvoke helpers

    def get_r_implfunc(self):
        raise TyperError("%s has no corresponding implementation function representation" % (self,))

    def get_s_callable(self):
        raise TyperError("%s is not callable or cannot reconstruct a pbc annotation for itself" % (self,))


class SafeRepr(Repr):
    """ subclass of repr.Repr that limits the resulting size of repr()
        and includes information on exceptions raised during the call.
    """

    def repr(self, x):
        return self._callhelper(Repr.repr, self, x)

    def repr_unicode(self, x, level):
        # Strictly speaking wrong on narrow builds
        def repr(u):
            if "'" not in u:
                return py.builtin._totext("'%s'") % u
            elif '"' not in u:
                return py.builtin._totext('"%s"') % u
            else:
                return py.builtin._totext("'%s'") % u.replace("'", r"\'")

        repr = builtin_repr
        # ^^^ it's very annoying to display 'xx' instead of u'xx' when
        # the difference can be essential, particularly in PyPy

        s = repr(x[:self.maxstring])
        if len(s) > self.maxstring:
            i = max(0, (self.maxstring - 3) // 2)
            j = max(0, self.maxstring - 3 - i)
            s = repr(x[:i] + x[len(x) - j:])
            s = s[:i] + '...' + s[len(s) - j:]
        return s

    def repr_instance(self, x, level):
        return self._callhelper(builtin_repr, x)

    def _callhelper(self, call, x, *args):
        try:
            # Try the vanilla repr and make sure that the result is a string
            s = call(x, *args)
        except _sysex:
            raise
        except:
            cls, e, tb = exc_info()
            exc_name = getattr(cls, '__name__', 'unknown')
            try:
                exc_info = str(e)
            except _sysex:
                raise
            except:
                exc_info = 'unknown'
            return '<[%s("%s") raised in repr()] %s object at 0x%x>' % (
                exc_name, exc_info, x.__class__.__name__, id(x))
        else:
            if len(s) > self.maxsize:
                i = max(0, (self.maxsize - 3) // 2)
                j = max(0, self.maxsize - 3 - i)
                s = s[:i] + '...' + s[len(s) - j:]
            return s


def saferepr(obj, maxsize=240):
    """ return a size-limited safe repr-string for the given object.
    Failing __repr__ functions of user instances will be represented
    with a short exception info and 'saferepr' generally takes
    care to never raise exceptions itself.  This function is a wrapper
    around the Repr/reprlib functionality of the standard 2.6 lib.
    """
    # review exception handling
    srepr = SafeRepr()
    srepr.maxstring = maxsize
    srepr.maxsize = maxsize
    srepr.maxother = 160
    return srepr.repr(obj)


def getsource(obj, **kwargs):
    obj = getrawcode(obj)
    try:
        strsrc = inspect.getsource(obj)
    except IndentationError:
        strsrc = "\"Buggy python version consider upgrading, cannot get source\""
    assert isinstance(strsrc, str)
    return Source(strsrc, **kwargs)


def getrawcode(obj, trycall=True):
    """ return code object for given function. """
    try:
        return obj.__code__
    except AttributeError:
        obj = getattr(obj, 'im_func', obj)
        obj = getattr(obj, 'func_code', obj)
        obj = getattr(obj, 'f_code', obj)
        obj = getattr(obj, '__code__', obj)
        if trycall and not hasattr(obj, 'co_firstlineno'):
            if hasattr(obj, '__call__') and not py.std.inspect.isclass(obj):
                x = getrawcode(obj.__call__, trycall=False)
                if hasattr(x, 'co_firstlineno'):
                    return x
        return obj


def _format_explanation(explanation):
    """This formats an explanation

    Normally all embedded newlines are escaped, however there are
    three exceptions: \n{, \n} and \n~.  The first two are intended
    cover nested explanations, see function and attribute explanations
    for examples (.visit_Call(), visit_Attribute()).  The last one is
    for when one explanation needs to span multiple lines, e.g. when
    displaying diffs.
    """
    raw_lines = (explanation or '').split('\n')
    # escape newlines not followed by {, } and ~
    lines = [raw_lines[0]]
    for l in raw_lines[1:]:
        if l.startswith('{') or l.startswith('}') or l.startswith('~'):
            lines.append(l)
        else:
            lines[-1] += '\\n' + l

    result = lines[:1]
    stack = [0]
    stackcnt = [0]
    for line in lines[1:]:
        if line.startswith('{'):
            if stackcnt[-1]:
                s = 'and   '
            else:
                s = 'where '
            stack.append(len(result))
            stackcnt[-1] += 1
            stackcnt.append(0)
            result.append(' +' + '  ' * (len(stack) - 1) + s + line[1:])
        elif line.startswith('}'):
            assert line.startswith('}')
            stack.pop()
            stackcnt.pop()
            result[stack[-1]] += line[1:]
        else:
            assert line.startswith('~')
            result.append('  ' * len(stack) + line[1:])
    assert len(stack) == 1
    return '\n'.join(result)


def deindent(lines, offset=None):
    if offset is None:
        for line in lines:
            line = line.expandtabs()
            s = line.lstrip()
            if s:
                offset = len(line) - len(s)
                break
        else:
            offset = 0
    if offset == 0:
        return list(lines)
    newlines = []

    def readline_generator(lines):
        for line in lines:
            yield line + '\n'
        while True:
            yield ''

    it = readline_generator(lines)

    try:
        for _, _, (sline, _), (eline, _), _ in tokenize.generate_tokens(lambda: next(it)):
            if sline > len(lines):
                break  # End of input reached
            if sline > len(newlines):
                line = lines[sline - 1].expandtabs()
                if line.lstrip() and line[:offset].isspace():
                    line = line[offset:]  # Deindent
                newlines.append(line)

            for i in range(sline, eline):
                # Don't deindent continuing lines of
                # multiline tokens (i.e. multiline strings)
                newlines.append(lines[i])
    except (IndentationError, tokenize.TokenError):
        pass
    # Add any lines we didn't see. E.g. if an exception was raised.
    newlines.extend(lines[len(newlines):])
    return newlines

def getstatementrange_ast(lineno, source, assertion=False, astnode=None):
    if astnode is None:
        content = str(source)
        if version_info < (2,7):
            content += "\n"
        try:
            astnode = compile(content, "source", "exec", 1024)  # 1024 for AST
        except ValueError:
            start, end = getstatementrange_old(lineno, source, assertion)
            return None, start, end
    start, end = get_statement_startend(lineno, getnodelist(astnode))
    # we need to correct the end:
    # - ast-parsing strips comments
    # - else statements do not have a separate lineno
    # - there might be empty lines
    # - we might have lesser indented code blocks at the end
    if end is None:
        end = len(source.lines)

    if end > start + 1:
        # make sure we don't span differently indented code blocks
        # by using the BlockFinder helper used which inspect.getsource() uses itself
        block_finder = inspect.BlockFinder()
        # if we start with an indented line, put blockfinder to "started" mode
        block_finder.started = source.lines[start][0].isspace()
        it = ((x + "\n") for x in source.lines[start:end])
        try:
            for tok in tokenize.generate_tokens(lambda: next(it)):
                block_finder.tokeneater(*tok)
        except (inspect.EndOfBlock, IndentationError) as e:
            end = block_finder.last + start
        #except Exception:
        #    pass

    # the end might still point to a comment, correct it
    while end:
        line = source.lines[end - 1].lstrip()
        if line.startswith("#"):
            end -= 1
        else:
            break
    return astnode, start, end

def getstatementrange_old(lineno, source, assertion=False):
    """ return (start, end) tuple which spans the minimal
        statement region which containing the given lineno.
        raise an IndexError if no such statementrange can be found.
    """
    # XXX this logic is only used on python2.4 and below
    # 1. find the start of the statement
    from codeop import compile_command
    for start in range(lineno, -1, -1):
        if assertion:
            line = source.lines[start]
            # the following lines are not fully tested, change with care
            if 'super' in line and 'self' in line and '__init__' in line:
                raise IndexError("likely a subclass")
            if "assert" not in line and "raise" not in line:
                continue
        trylines = source.lines[start:lineno+1]
        # quick hack to prepare parsing an indented line with
        # compile_command() (which errors on "return" outside defs)
        trylines.insert(0, 'def xxx():')
        trysource = '\n '.join(trylines)
        #              ^ space here
        try:
            compile_command(trysource)
        except (SyntaxError, OverflowError, ValueError):
            continue

        # 2. find the end of the statement
        for end in range(lineno+1, len(source)+1):
            trysource = source[start:end]
            if trysource.isparseable():
                return start, end
    raise SyntaxError("no valid source range around line %d " % (lineno,))

def get_statement_startend(lineno, nodelist):
    from bisect import bisect_right
    # lineno starts at 0
    nextlineno = None
    while 1:
        lineno_list = [x.lineno-1 for x in nodelist] # ast indexes start at 1
        #print lineno_list, [vars(x) for x in nodelist]
        insert_index = bisect_right(lineno_list, lineno)
        if insert_index >= len(nodelist):
            insert_index -= 1
        elif lineno < (nodelist[insert_index].lineno - 1) and insert_index > 0:
            insert_index -= 1
            assert lineno >= (nodelist[insert_index].lineno - 1)
        nextnode = nodelist[insert_index]

        try:
            nextlineno = nodelist[insert_index+1].lineno - 1
        except IndexError:
            pass
        lastnodelist = nodelist
        nodelist = getnodelist(nextnode)
        if not nodelist:
            start, end = nextnode.lineno-1, nextlineno
            start = min(lineno, start)
            assert start <= lineno  and (end is None or lineno < end)
            return start, end

def getnodelist(node):
    import _ast
    l = []
    #print "node", node, "fields", node._fields, "lineno", getattr(node, "lineno", 0) - 1
    for subname in "test", "type", "body", "handlers", "orelse", "finalbody":
        attr = getattr(node, subname, None)
        if attr is not None:
            if isinstance(attr, list):
                l.extend(attr)
            elif hasattr(attr, "lineno"):
                l.append(attr)
    return l

def findsource(obj):
    try:
        sourcelines, lineno = inspect.findsource(obj)
    except _sysex:
        raise
    except:
        return None, -1
    source = Source()
    source.lines = [line.rstrip() for line in sourcelines]
    return source, lineno


_sysex = (KeyboardInterrupt, SystemExit, MemoryError, GeneratorExit)
