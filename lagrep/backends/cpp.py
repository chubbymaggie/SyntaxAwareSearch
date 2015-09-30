from clang.cindex import TranslationUnit
from clang.cindex import CursorKind
from ..kinds import Kinds
from .utils import get_cursors


def find_candidates(filename, ast):
    """ Find patterns in 'filename' matching 'ast'
    """

    tu = TranslationUnit.from_source(filename)
    for cursor in resolve_ast(tu, ast):
        yield cursor.location.line


def is_kind(ast):
    if not isinstance(ast, list):
        return ast in Kinds.__dict__.values()
    else:
        return ast[0] in Kinds.__dict__.values()
    return False


def is_operator(ast):
    return not is_kind(ast)


def resolve_ast(tu, ast):
    """ Yields cursors matching the pattern in 'ast'
    """
    if is_kind(ast):
        for cursor in find_cursors_by_kind(tu, ast):
            yield cursor
    else:
        for cursor in find_cursors_by_operator(tu, ast):
            yield cursor


def recursive_children(cursor):
    for child in cursor.get_children():
        for grandchild in recursive_children(child):
            yield grandchild
        yield child


def find_cursors_by_operator(tu, ast):
    operator = ast[0]
    if operator.name == "OR":
        for cursor in resolve_ast(tu, ast[1]):
            yield cursor
        for cursor in resolve_ast(tu, ast[2]):
            yield cursor
    if operator.name == "CHILD":
        for cursor in resolve_ast(tu, ast[1]):
            for child in recursive_children(cursor):
                if child in resolve_ast(tu, ast[2]):
                    yield cursor


def find_cursors_by_kind(tu, kind, data=None):
    KIND_MAPPING = {
        Kinds.FUNCTION: [CursorKind.FUNCTION_DECL,
                         CursorKind.CXX_METHOD],
        Kinds.TYPE: [CursorKind.CLASS_DECL,
                     CursorKind.STRUCT_DECL],
        Kinds.VARIABLE: [CursorKind.VAR_DECL]
    }
    search_kind = None
    data = None
    if isinstance(kind, list):
        search_kind = kind[0]
        if kind[1].name == "EQUAL":
            data = kind[2].value
    else:
        search_kind = kind
    cursor_kind = KIND_MAPPING[search_kind]
    cursors = get_cursors(tu, data)
    for cursor in cursors:
        if cursor.kind in cursor_kind:
            yield cursor