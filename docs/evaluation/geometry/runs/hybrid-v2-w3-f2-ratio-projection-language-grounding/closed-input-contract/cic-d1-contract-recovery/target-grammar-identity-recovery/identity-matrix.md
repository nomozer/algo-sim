# Namespace identity matrix

| case | operands | schema /1 | schema /2 | /3 | planner | /4 |
|---|---|---|---|---|---|---|
| I.forward | {"segment": ["A", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.reverse | {"segment": ["pr::A", "A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.qualified | {"segment": ["pr::A", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.prime | {"segment": ["A'", "pr::A'"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.trimmed | {"segment": [" A ", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.distinct | {"segment": ["A", "pr::B"]} | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | REQUEST_NOT_ANSWERED |
| I.unknown_namespace | {"segment": ["ghost::A", "B"]} | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| I.malformed | {"segment": ["pr:::A", "B"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.unicode_0x2032 | {"segment": ["A′", "pr::A'"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.unicode_0x2019 | {"segment": ["A’", "pr::A'"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.bound_alias | {"segment": ["X", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.bound_distinct | {"segment": ["pr::A", "pr::B"]} | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY | BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY |
| I.different_solids_same_label | {"segment": ["pr::A", "other::A"]} | VALID | VALID | AMBIGUOUS_REFERENCE | AMBIGUOUS_REFERENCE | AMBIGUOUS_REFERENCE |
| I.ambiguous | {"segment": ["A", "pr::B"]} | AMBIGUOUS_REFERENCE | AMBIGUOUS_REFERENCE | AMBIGUOUS_REFERENCE | AMBIGUOUS_REFERENCE | AMBIGUOUS_REFERENCE |
| I.scoped_nonidentity | {"segment": ["A", "other::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.hyphen | {"segment": ["A", "pyr-1::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.constructed_alias | {"segment": ["M", "pyr1::M"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.constructed_distinct | {"segment": ["M", "pyr1::B"]} | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY | BRIDGE_UNSUPPORTED_QUALIFIED_IDENTITY |
| I.derived_apex_alias | {"segment": ["S", "top_pyramid::S"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.derived_constructed_alias | {"segment": ["M", "top_pyramid::M"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.derived_distinct | {"segment": ["top_pyramid::S", "M"]} | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| I.operand_line | {"line": ["A", "pr::A"], "plane": ["A", "B", "C"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.operand_line1 | {"line1": ["A", "pr::A"], "line2": ["B", "C"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.operand_line2 | {"line1": ["A", "B"], "line2": ["A", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.operand_plane | {"point": "A'", "plane": ["A", "B", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.operand_plane1 | {"plane1": ["A", "B", "pr::A"], "plane2": ["A'", "B'", "C'"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.operand_plane2 | {"plane1": ["A", "B", "C"], "plane2": ["A", "B", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| I.operand_polygon | {"polygon": ["A", "B", "pr::A"]} | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
