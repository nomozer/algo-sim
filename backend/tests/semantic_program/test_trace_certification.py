# -*- coding: utf-8 -*-
"""TRACE_CERTIFICATION: Chứng nhận tương đương 100% giữa AST Interpreter và Independent Oracle."""
import pytest
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from .fixtures_coverage_18 import (
    P01_STACK_BRACKET,
    P02_FIND_MAX,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
    P05_SELECTION_SORT,
    P06_INSERTION_SORT,
    P07_TWO_SUM_SORTED,
    P08_PALINDROME,
    P09_GRAPH_BFS,
    P10_REVERSE_STRING_STACK,
    P11_TREE_PREORDER,
    P12_TREE_INORDER,
    P13_DECIMAL_TO_BINARY,
    P14_BITWISE_CHECK,
    P15_MATRIX_TRAVERSAL,
    P16_DFA_LEXER,
    P17_PREFIX_SUM,
    P18_FREQUENCY_COUNT,
)
from .execution_oracles import (
    oracle_stack_bracket,
    oracle_find_max,
    oracle_binary_search,
    oracle_bubble_sort,
    oracle_selection_sort,
    oracle_insertion_sort,
    oracle_two_sum_sorted,
    oracle_palindrome,
    oracle_graph_bfs,
    oracle_reverse_string,
    oracle_tree_preorder,
    oracle_tree_inorder,
    oracle_decimal_to_binary,
    oracle_bitwise_check,
    oracle_matrix_sum,
    oracle_dfa_lexer,
    oracle_prefix_sum,
    oracle_frequency_count,
)


def test_certify_p01_stack_bracket_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P01_STACK_BRACKET)
    raw_input = P01_STACK_BRACKET.memory_declarations[0].initial_value
    oracle_res = oracle_stack_bracket(raw_input)

    assert res.final_memory["result"] == oracle_res["result"]
    assert res.final_memory["stack"] == oracle_res["final_stack"]


def test_certify_p02_find_max_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P02_FIND_MAX)
    raw_input = P02_FIND_MAX.memory_declarations[0].initial_value
    oracle_res = oracle_find_max(raw_input)

    assert res.final_memory["max_val"] == oracle_res["max_val"]
    assert res.final_memory["max_idx"] == oracle_res["max_idx"]


def test_certify_p03_binary_search_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P03_BINARY_SEARCH)
    arr = P03_BINARY_SEARCH.memory_declarations[0].initial_value
    target = P03_BINARY_SEARCH.memory_declarations[1].initial_value
    oracle_res = oracle_binary_search(arr, target)

    assert res.final_memory["found_idx"] == oracle_res["found_idx"]


def test_certify_p04_bubble_sort_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P04_BUBBLE_SORT)
    arr = P04_BUBBLE_SORT.memory_declarations[0].initial_value
    oracle_res = oracle_bubble_sort(arr)

    assert res.final_memory["arr"] == oracle_res["arr"]


def test_certify_p05_selection_sort_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P05_SELECTION_SORT)
    arr = P05_SELECTION_SORT.memory_declarations[0].initial_value
    oracle_res = oracle_selection_sort(arr)

    assert res.final_memory["arr"] == oracle_res["arr"]


def test_certify_p06_insertion_sort_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P06_INSERTION_SORT)
    arr = P06_INSERTION_SORT.memory_declarations[0].initial_value
    oracle_res = oracle_insertion_sort(arr)

    assert res.final_memory["arr"] == oracle_res["arr"]


def test_certify_p07_two_sum_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P07_TWO_SUM_SORTED)
    arr = P07_TWO_SUM_SORTED.memory_declarations[0].initial_value
    target = P07_TWO_SUM_SORTED.memory_declarations[1].initial_value
    oracle_res = oracle_two_sum_sorted(arr, target)

    assert res.final_memory["found"] == oracle_res["found"]
    assert res.final_memory["curr_sum"] == oracle_res["curr_sum"]


def test_certify_p08_palindrome_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P08_PALINDROME)
    chars = P08_PALINDROME.memory_declarations[0].initial_value
    oracle_res = oracle_palindrome(chars)

    assert res.final_memory["is_pal"] == oracle_res["is_pal"]


def test_certify_p09_graph_bfs_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P09_GRAPH_BFS)
    graph = P09_GRAPH_BFS.memory_declarations[0].initial_value
    oracle_res = oracle_graph_bfs(graph, "1")

    assert res.final_memory["order"] == oracle_res["order"]


def test_certify_p10_reverse_string_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P10_REVERSE_STRING_STACK)
    chars = P10_REVERSE_STRING_STACK.memory_declarations[0].initial_value
    oracle_res = oracle_reverse_string(chars)

    assert res.final_memory["output_chars"] == oracle_res["output_chars"]


def test_certify_p11_tree_preorder_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P11_TREE_PREORDER)
    root = P11_TREE_PREORDER.memory_declarations[0].initial_value
    oracle_res = oracle_tree_preorder(root)

    assert res.final_memory["order"] == oracle_res["order"]


def test_certify_p12_tree_inorder_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P12_TREE_INORDER)
    root = P12_TREE_INORDER.memory_declarations[0].initial_value
    oracle_res = oracle_tree_inorder(root)

    assert res.final_memory["order"] == oracle_res["order"]


def test_certify_p13_decimal_to_binary_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P13_DECIMAL_TO_BINARY)
    n = P13_DECIMAL_TO_BINARY.memory_declarations[0].initial_value
    oracle_res = oracle_decimal_to_binary(n)

    assert res.final_memory["binary_digits"] == oracle_res["binary_digits"]


def test_certify_p14_bitwise_check_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P14_BITWISE_CHECK)
    num = P14_BITWISE_CHECK.memory_declarations[0].initial_value
    k = P14_BITWISE_CHECK.memory_declarations[1].initial_value
    oracle_res = oracle_bitwise_check(num, k)

    assert res.final_memory["bit_is_set"] == oracle_res["bit_is_set"]


def test_certify_p15_matrix_sum_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P15_MATRIX_TRAVERSAL)
    grid = P15_MATRIX_TRAVERSAL.memory_declarations[0].initial_value
    oracle_res = oracle_matrix_sum(grid)

    assert res.final_memory["total_sum"] == oracle_res["total_sum"]


def test_certify_p16_dfa_lexer_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P16_DFA_LEXER)
    chars = P16_DFA_LEXER.memory_declarations[0].initial_value
    trans = P16_DFA_LEXER.memory_declarations[2].initial_value
    oracle_res = oracle_dfa_lexer(chars, trans)

    assert res.final_memory["is_valid"] == oracle_res["is_valid"]


def test_certify_p17_prefix_sum_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P17_PREFIX_SUM)
    arr = P17_PREFIX_SUM.memory_declarations[0].initial_value
    oracle_res = oracle_prefix_sum(arr)

    assert res.final_memory["pref"] == oracle_res["pref"]


def test_certify_p18_frequency_count_parity():
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P18_FREQUENCY_COUNT)
    text = P18_FREQUENCY_COUNT.memory_declarations[0].initial_value
    oracle_res = oracle_frequency_count(text)

    assert res.final_memory["freq"] == oracle_res["freq"]
