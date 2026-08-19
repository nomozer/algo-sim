# -*- coding: utf-8 -*-
"""Independent Execution Oracles: Nguồn chân lý (Ground Truth) độc lập bằng Python thuần túy.

Các hàm trong file này hoàn toàn tách rời khỏi AST interpreter và SemanticProgramSpec,
được dùng để đối soát và chứng nhận tính đúng đắn của quá trình thực thi.
"""
from typing import Any


def oracle_stack_bracket(chars: list[str]) -> dict[str, Any]:
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    result = "HỢP LỆ"
    for c in chars:
        if c in pairs:
            stack.append(c)
        else:
            if not stack or pairs.get(stack[-1]) != c:
                result = "KHÔNG HỢP LỆ"
                break
            stack.pop()
    if stack:
        result = "KHÔNG HỢP LỆ"
    return {"result": result, "final_stack": stack}


def oracle_find_max(arr: list[int]) -> dict[str, Any]:
    if not arr:
        return {"max_val": None, "max_idx": -1}
    max_val = arr[0]
    max_idx = 0
    for i in range(1, len(arr)):
        if arr[i] > max_val:
            max_val = arr[i]
            max_idx = i
    return {"max_val": max_val, "max_idx": max_idx}


def oracle_binary_search(arr: list[int], target: int) -> dict[str, Any]:
    left, right = 0, len(arr) - 1
    found_idx = -1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            found_idx = mid
            break
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return {"found_idx": found_idx}


def oracle_bubble_sort(arr: list[int]) -> dict[str, Any]:
    a = list(arr)
    n = len(a)
    for i in range(n - 1):
        swapped = False
        for j in range(n - 1 - i):
            if a[j] > a[j + 1]:
                a[j], a[j + 1] = a[j + 1], a[j]
                swapped = True
        if not swapped:
            break
    return {"arr": a}


def oracle_selection_sort(arr: list[int]) -> dict[str, Any]:
    a = list(arr)
    n = len(a)
    for i in range(n - 1):
        min_idx = i
        for j in range(i + 1, n):
            if a[j] < a[min_idx]:
                min_idx = j
        if min_idx != i:
            a[i], a[min_idx] = a[min_idx], a[i]
    return {"arr": a}


def oracle_insertion_sort(arr: list[int]) -> dict[str, Any]:
    a = list(arr)
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return {"arr": a}


def oracle_two_sum_sorted(arr: list[int], target: int) -> dict[str, Any]:
    left, right = 0, len(arr) - 1
    found = False
    curr_sum = 0
    while left < right:
        curr_sum = arr[left] + arr[right]
        if curr_sum == target:
            found = True
            break
        elif curr_sum < target:
            left += 1
        else:
            right -= 1
    return {"found": found, "curr_sum": curr_sum}


def oracle_palindrome(chars: list[str]) -> dict[str, Any]:
    left, right = 0, len(chars) - 1
    is_pal = True
    while left < right:
        if chars[left] != chars[right]:
            is_pal = False
            break
        left += 1
        right -= 1
    return {"is_pal": is_pal}


def oracle_graph_bfs(graph: dict[str, list[str]], start_node: str) -> dict[str, Any]:
    q = [start_node]
    visited = {start_node}
    order = []
    while q:
        u = q.pop(0)
        order.append(u)
        for v in graph.get(u, []):
            if v not in visited:
                visited.add(v)
                q.append(v)
    return {"order": order, "visited": list(visited)}


def oracle_reverse_string(chars: list[str]) -> dict[str, Any]:
    stack = list(chars)
    output = []
    while stack:
        output.append(stack.pop())
    return {"output_chars": output}


def oracle_tree_preorder(root: dict) -> dict[str, Any]:
    if not root:
        return {"order": []}
    stack = [root]
    order = []
    while stack:
        curr = stack.pop()
        order.append(curr["val"])
        if curr.get("right"):
            stack.append(curr["right"])
        if curr.get("left"):
            stack.append(curr["left"])
    return {"order": order}


def oracle_tree_inorder(root: dict) -> dict[str, Any]:
    stack = []
    order = []
    curr = root
    while curr or stack:
        while curr:
            stack.append(curr)
            curr = curr.get("left")
        curr = stack.pop()
        order.append(curr["val"])
        curr = curr.get("right")
    return {"order": order}


def oracle_decimal_to_binary(n: int) -> dict[str, Any]:
    stack = []
    while n > 0:
        stack.append(n % 2)
        n = n // 2
    digits = []
    while stack:
        digits.append(stack.pop())
    return {"binary_digits": digits}


def oracle_bitwise_check(num: int, k: int) -> dict[str, Any]:
    bit_is_set = ((num >> k) & 1) == 1
    return {"bit_is_set": bit_is_set}


def oracle_matrix_sum(grid: list[list[int]]) -> dict[str, Any]:
    total_sum = sum(sum(row) for row in grid)
    return {"total_sum": total_sum}


def oracle_dfa_lexer(chars: list[str], transitions: dict[str, str]) -> dict[str, Any]:
    state = "START"
    for ch in chars:
        key = f"{state}:{ch}"
        state = transitions.get(key, "ERROR")
        if state == "ERROR":
            break
    return {"is_valid": state == "ID", "final_state": state}


def oracle_prefix_sum(arr: list[int]) -> dict[str, Any]:
    if not arr:
        return {"pref": []}
    pref = [arr[0]]
    for i in range(1, len(arr)):
        pref.append(pref[i - 1] + arr[i])
    return {"pref": pref}


def oracle_frequency_count(text: list[str]) -> dict[str, Any]:
    freq = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    return {"freq": freq}
