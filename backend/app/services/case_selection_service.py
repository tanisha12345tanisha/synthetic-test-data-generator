import random


def build_case_pool(case_distribution):
    case_pool = []

    distribution_dict = case_distribution.model_dump()

    for case_type, percentage in distribution_dict.items():
        case_pool.extend([case_type] * percentage)

    return case_pool


def select_case_type(case_distribution):
    case_pool = build_case_pool(case_distribution)

    if not case_pool:
        return "normal"

    return random.choice(case_pool)


def get_case_labels(case_type):
    if case_type == "normal":
        return ["normal"]

    if case_type == "edge_case":
        return ["edge_case"]

    if case_type == "corner_case":
        return ["corner_case"]

    if case_type == "boundary_case":
        return ["boundary_case"]

    if case_type == "invalid_case":
        return ["invalid_case"]

    if case_type == "duplicate_case":
        return ["duplicate_case"]

    if case_type == "null_case":
        return ["null_case"]

    if case_type == "format_violation_case":
        return ["format_violation_case", "invalid_case"]

    if case_type == "range_violation_case":
        return ["range_violation_case", "invalid_case"]

    if case_type == "length_violation_case":
        return ["length_violation_case", "invalid_case"]

    return ["mixed_case"]