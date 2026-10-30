# Target grammar matrix — all frozen cases

Registered alternatives are fixed in registration.json. Schema validity and route support are separate. Source and exact answer receipts: observed-main/pre/red/green.json. Internal errors below are unresolved F7, never counted as supported capability.

| case | kind | target keys | class | schema /1 | schema /2 | /3 | planner | /4 |
|---|---|---|---|---|---|---|---|---|
| G.distance.segment.plain | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.segment.goal_sid | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.segment.goal_sid_null | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.segment.goal_sid_unknown | distance | segment | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.segment.qualified | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.segment.foreign_ns | distance | segment | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.segment.+solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid_id | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid_id.goal_sid | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+notation | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+notation.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+both | distance | segment, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+both.goal_sid | distance | segment, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+unknown_solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+unknown_solid.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+unknown_solid_id | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+unknown_solid_id.goal_sid | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+null_solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+null_solid.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+null_solid_id | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+null_solid_id.goal_sid | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+extra_key | distance | segment, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+extra_key.goal_sid | distance | segment, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+section_id | distance | segment, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+section_id.goal_sid | distance | segment, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid_int | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid_int.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid_id_list | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+solid_id_list.goal_sid | distance | segment, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+canonical_notation | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+canonical_notation.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+empty_solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.+empty_solid.goal_sid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.plain | distance | point, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_plane.goal_sid | distance | point, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_plane.goal_sid_null | distance | point, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_plane.goal_sid_unknown | distance | point, plane | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.point_plane.qualified | distance | point, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_plane.foreign_ns | distance | point, plane | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.point_plane.+solid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid_id | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid_id.goal_sid | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+notation | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+notation.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+both | distance | point, plane, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+both.goal_sid | distance | point, plane, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+unknown_solid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+unknown_solid.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+unknown_solid_id | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+unknown_solid_id.goal_sid | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+null_solid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+null_solid.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+null_solid_id | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+null_solid_id.goal_sid | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+extra_key | distance | point, plane, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+extra_key.goal_sid | distance | point, plane, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+section_id | distance | point, plane, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+section_id.goal_sid | distance | point, plane, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid_int | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid_int.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid_id_list | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+solid_id_list.goal_sid | distance | point, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+canonical_notation | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+canonical_notation.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+empty_solid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.+empty_solid.goal_sid | distance | point, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.half+solid | distance | point, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.half+solid_id | distance | plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.plain | distance | point, line | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_line.goal_sid | distance | point, line | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_line.goal_sid_null | distance | point, line | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_line.goal_sid_unknown | distance | point, line | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.point_line.qualified | distance | point, line | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.point_line.foreign_ns | distance | point, line | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.point_line.+solid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid_id | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid_id.goal_sid | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+notation | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+notation.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+both | distance | point, line, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+both.goal_sid | distance | point, line, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+unknown_solid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+unknown_solid.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+unknown_solid_id | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+unknown_solid_id.goal_sid | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+null_solid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+null_solid.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+null_solid_id | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+null_solid_id.goal_sid | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+extra_key | distance | point, line, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+extra_key.goal_sid | distance | point, line, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+section_id | distance | point, line, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+section_id.goal_sid | distance | point, line, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid_int | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid_int.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid_id_list | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+solid_id_list.goal_sid | distance | point, line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+canonical_notation | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+canonical_notation.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+empty_solid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.+empty_solid.goal_sid | distance | point, line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.half+solid | distance | point, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_line.half+solid_id | distance | line, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.plain | distance | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line1_line2.goal_sid | distance | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line1_line2.goal_sid_null | distance | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line1_line2.goal_sid_unknown | distance | line1, line2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.line1_line2.qualified | distance | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line1_line2.foreign_ns | distance | line1, line2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.line1_line2.+solid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid_id | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid_id.goal_sid | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+notation | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+notation.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+both | distance | line1, line2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+both.goal_sid | distance | line1, line2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+unknown_solid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+unknown_solid.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+unknown_solid_id | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+unknown_solid_id.goal_sid | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+null_solid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+null_solid.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+null_solid_id | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+null_solid_id.goal_sid | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+extra_key | distance | line1, line2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+extra_key.goal_sid | distance | line1, line2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+section_id | distance | line1, line2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+section_id.goal_sid | distance | line1, line2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid_int | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid_int.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid_id_list | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+solid_id_list.goal_sid | distance | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+canonical_notation | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+canonical_notation.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+empty_solid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.+empty_solid.goal_sid | distance | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.half+solid | distance | line1, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line1_line2.half+solid_id | distance | line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.plain | distance | line, plane | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line_plane.goal_sid | distance | line, plane | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line_plane.goal_sid_null | distance | line, plane | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line_plane.goal_sid_unknown | distance | line, plane | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.line_plane.qualified | distance | line, plane | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.line_plane.foreign_ns | distance | line, plane | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.line_plane.+solid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid_id | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid_id.goal_sid | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+notation | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+notation.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+both | distance | line, plane, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+both.goal_sid | distance | line, plane, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+unknown_solid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+unknown_solid.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+unknown_solid_id | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+unknown_solid_id.goal_sid | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+null_solid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+null_solid.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+null_solid_id | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+null_solid_id.goal_sid | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+extra_key | distance | line, plane, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+extra_key.goal_sid | distance | line, plane, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+section_id | distance | line, plane, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+section_id.goal_sid | distance | line, plane, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid_int | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid_int.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid_id_list | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+solid_id_list.goal_sid | distance | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+canonical_notation | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+canonical_notation.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+empty_solid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.+empty_solid.goal_sid | distance | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.half+solid | distance | line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.line_plane.half+solid_id | distance | plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.plain | distance | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.plane1_plane2.goal_sid | distance | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.plane1_plane2.goal_sid_null | distance | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.plane1_plane2.goal_sid_unknown | distance | plane1, plane2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.plane1_plane2.qualified | distance | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.distance.plane1_plane2.foreign_ns | distance | plane1, plane2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.distance.plane1_plane2.+solid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid_id | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid_id.goal_sid | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+notation | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+notation.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+both | distance | plane1, plane2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+both.goal_sid | distance | plane1, plane2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+unknown_solid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+unknown_solid.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+unknown_solid_id | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+unknown_solid_id.goal_sid | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+null_solid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+null_solid.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+null_solid_id | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+null_solid_id.goal_sid | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+extra_key | distance | plane1, plane2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+extra_key.goal_sid | distance | plane1, plane2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+section_id | distance | plane1, plane2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+section_id.goal_sid | distance | plane1, plane2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid_int | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid_int.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid_id_list | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+solid_id_list.goal_sid | distance | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+canonical_notation | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+canonical_notation.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+empty_solid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.+empty_solid.goal_sid | distance | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.half+solid | distance | plane1, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.plane1_plane2.half+solid_id | distance | plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.plain | angle | line, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line_plane.goal_sid | angle | line, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line_plane.goal_sid_null | angle | line, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line_plane.goal_sid_unknown | angle | line, plane | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.angle.line_plane.qualified | angle | line, plane | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line_plane.foreign_ns | angle | line, plane | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.angle.line_plane.+solid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid_id | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid_id.goal_sid | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+notation | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+notation.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+both | angle | line, plane, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+both.goal_sid | angle | line, plane, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+unknown_solid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+unknown_solid.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+unknown_solid_id | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+unknown_solid_id.goal_sid | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+null_solid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+null_solid.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+null_solid_id | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+null_solid_id.goal_sid | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+extra_key | angle | line, plane, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+extra_key.goal_sid | angle | line, plane, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+section_id | angle | line, plane, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+section_id.goal_sid | angle | line, plane, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid_int | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid_int.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid_id_list | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+solid_id_list.goal_sid | angle | line, plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+canonical_notation | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+canonical_notation.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+empty_solid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.+empty_solid.goal_sid | angle | line, plane, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.half+solid | angle | line, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line_plane.half+solid_id | angle | plane, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.plain | angle | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line1_line2.goal_sid | angle | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line1_line2.goal_sid_null | angle | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line1_line2.goal_sid_unknown | angle | line1, line2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.angle.line1_line2.qualified | angle | line1, line2 | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.line1_line2.foreign_ns | angle | line1, line2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.angle.line1_line2.+solid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid_id | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid_id.goal_sid | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+notation | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+notation.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+both | angle | line1, line2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+both.goal_sid | angle | line1, line2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+unknown_solid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+unknown_solid.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+unknown_solid_id | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+unknown_solid_id.goal_sid | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+null_solid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+null_solid.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+null_solid_id | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+null_solid_id.goal_sid | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+extra_key | angle | line1, line2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+extra_key.goal_sid | angle | line1, line2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+section_id | angle | line1, line2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+section_id.goal_sid | angle | line1, line2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid_int | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid_int.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid_id_list | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+solid_id_list.goal_sid | angle | line1, line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+canonical_notation | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+canonical_notation.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+empty_solid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.+empty_solid.goal_sid | angle | line1, line2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.half+solid | angle | line1, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.line1_line2.half+solid_id | angle | line2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.plain | angle | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.plane1_plane2.goal_sid | angle | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.plane1_plane2.goal_sid_null | angle | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.plane1_plane2.goal_sid_unknown | angle | plane1, plane2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.angle.plane1_plane2.qualified | angle | plane1, plane2 | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | SERVED |
| G.angle.plane1_plane2.foreign_ns | angle | plane1, plane2 | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.angle.plane1_plane2.+solid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid_id | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid_id.goal_sid | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+notation | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+notation.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+both | angle | plane1, plane2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+both.goal_sid | angle | plane1, plane2, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+unknown_solid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+unknown_solid.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+unknown_solid_id | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+unknown_solid_id.goal_sid | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+null_solid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+null_solid.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+null_solid_id | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+null_solid_id.goal_sid | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+extra_key | angle | plane1, plane2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+extra_key.goal_sid | angle | plane1, plane2, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+section_id | angle | plane1, plane2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+section_id.goal_sid | angle | plane1, plane2, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid_int | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid_int.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid_id_list | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+solid_id_list.goal_sid | angle | plane1, plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+canonical_notation | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+canonical_notation.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+empty_solid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.+empty_solid.goal_sid | angle | plane1, plane2, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.half+solid | angle | plane1, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.plane1_plane2.half+solid_id | angle | plane2, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.plain | area | polygon | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| G.area.polygon.goal_sid | area | polygon | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| G.area.polygon.goal_sid_null | area | polygon | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| G.area.polygon.goal_sid_unknown | area | polygon | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.area.polygon.qualified | area | polygon | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| G.area.polygon.foreign_ns | area | polygon | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| G.area.polygon.+solid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid_id | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid_id.goal_sid | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+notation | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+notation.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+both | area | polygon, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+both.goal_sid | area | polygon, solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+unknown_solid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+unknown_solid.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+unknown_solid_id | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+unknown_solid_id.goal_sid | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+null_solid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+null_solid.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+null_solid_id | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+null_solid_id.goal_sid | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+extra_key | area | polygon, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+extra_key.goal_sid | area | polygon, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+section_id | area | polygon, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+section_id.goal_sid | area | polygon, section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid_int | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid_int.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid_id_list | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+solid_id_list.goal_sid | area | polygon, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+canonical_notation | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+canonical_notation.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+empty_solid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.area.polygon.+empty_solid.goal_sid | area | polygon, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.dup_qualified | distance | segment | F2 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.dup_qualified | distance | point, plane | F2 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point_plane.dup_qual4 | distance | point, plane | F2 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.string | distance | segment | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.segment.three | distance | segment | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point.list | distance | point, plane | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.point.int | distance | point, plane | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.nested_obj | distance | segment | F2 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.only_solid | distance | solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.only_solid_id | distance | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.empty | distance |  | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.distance.mixed_alts | distance | segment, point, plane | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.segment | angle | segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| G.angle.point_plane | angle | point, plane | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.solid | volume | solid | CONTROL | VALID | VALID | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE |
| V.volume.solid.goal_sid | volume | solid | CONTROL | VALID | VALID | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE |
| V.volume.solid_id | volume | solid_id | CONTROL | VALID | VALID | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE |
| V.volume.solid_id.goal_sid | volume | solid_id | CONTROL | VALID | VALID | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE |
| V.volume.both | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.both.goal_sid | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.notation | volume | solid | CONTROL | VALID | VALID | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE |
| V.volume.notation.goal_sid | volume | solid | CONTROL | VALID | VALID | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE | NOT_ASKED_IN_SOURCE |
| V.volume.notation+id | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.notation+id.goal_sid | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.conflict | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.conflict.goal_sid | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.unknown | volume | solid | CONTROL | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID |
| V.volume.unknown.goal_sid | volume | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.volume.unknown_id | volume | solid_id | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.volume.unknown_id.goal_sid | volume | solid_id | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.volume.extra | volume | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.extra.goal_sid | volume | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.segment+solid | volume | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.segment+solid.goal_sid | volume | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.null | volume | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.null.goal_sid | volume | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.int | volume | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.int.goal_sid | volume | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.empty_str | volume | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.empty_str.goal_sid | volume | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.volume.goal_sid_conflict | volume | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.area.solid | area | solid | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.area.solid.goal_sid | area | solid | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.area.solid_id | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.solid_id.goal_sid | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.both | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.both.goal_sid | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.notation | area | solid | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.area.notation.goal_sid | area | solid | CONTROL | VALID | VALID | INVALID_MATH_GOAL | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.area.notation+id | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.notation+id.goal_sid | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.conflict | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.conflict.goal_sid | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.unknown | area | solid | CONTROL | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID |
| V.area.unknown.goal_sid | area | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.area.unknown_id | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.unknown_id.goal_sid | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.extra | area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.extra.goal_sid | area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.segment+solid | area | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.segment+solid.goal_sid | area | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.null | area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.null.goal_sid | area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.int | area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.int.goal_sid | area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.empty_str | area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.empty_str.goal_sid | area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.area.goal_sid_conflict | area | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.radius.solid | radius | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.radius.solid.goal_sid | radius | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.radius.solid_id | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.solid_id.goal_sid | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.both | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.both.goal_sid | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.notation | radius | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.radius.notation.goal_sid | radius | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.radius.notation+id | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.notation+id.goal_sid | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.conflict | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.conflict.goal_sid | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.unknown | radius | solid | CONTROL | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID |
| V.radius.unknown.goal_sid | radius | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.radius.unknown_id | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.unknown_id.goal_sid | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.extra | radius | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.extra.goal_sid | radius | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.segment+solid | radius | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.segment+solid.goal_sid | radius | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.null | radius | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.null.goal_sid | radius | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.int | radius | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.int.goal_sid | radius | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.empty_str | radius | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.empty_str.goal_sid | radius | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.radius.goal_sid_conflict | radius | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.lateral_area.solid | lateral_area | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.lateral_area.solid.goal_sid | lateral_area | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.lateral_area.solid_id | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.solid_id.goal_sid | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.both | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.both.goal_sid | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.notation | lateral_area | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.lateral_area.notation.goal_sid | lateral_area | solid | CONTROL | VALID | VALID | ADAPTER_INTERNAL_ERROR | BRIDGE_UNSUPPORTED_MEASUREMENT | BRIDGE_UNSUPPORTED_MEASUREMENT |
| V.lateral_area.notation+id | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.notation+id.goal_sid | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.conflict | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.conflict.goal_sid | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.unknown | lateral_area | solid | CONTROL | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID | UNKNOWN_SOLID |
| V.lateral_area.unknown.goal_sid | lateral_area | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| V.lateral_area.unknown_id | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.unknown_id.goal_sid | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.extra | lateral_area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.extra.goal_sid | lateral_area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.segment+solid | lateral_area | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.segment+solid.goal_sid | lateral_area | solid, segment | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.null | lateral_area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.null.goal_sid | lateral_area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.int | lateral_area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.int.goal_sid | lateral_area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.empty_str | lateral_area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.empty_str.goal_sid | lateral_area | solid | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| V.lateral_area.goal_sid_conflict | lateral_area | solid | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| K.cyl.volume.solid | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.volume.solid_id | volume | solid_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.volume.both | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.volume.notation | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.volume.conflict | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.volume.section | volume | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.volume.section+solid | volume | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.volume.section+solid_id | volume | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.volume.extra | volume | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.volume.section.goal_sid | volume | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.solid | lateral_area | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.lateral_area.solid_id | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.both | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.notation | lateral_area | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.lateral_area.conflict | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.section | lateral_area | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.section+solid | lateral_area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.section+solid_id | lateral_area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.extra | lateral_area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.lateral_area.section.goal_sid | lateral_area | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.solid | radius | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.radius.solid_id | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.both | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.notation | radius | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.radius.conflict | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.section | radius | section_id | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.radius.section+solid | radius | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.section+solid_id | radius | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.extra | radius | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.radius.section.goal_sid | radius | section_id | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.area.solid | area | solid | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.area.solid_id | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.area.both | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.area.notation | area | solid | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.area.conflict | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.area.section | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.area.section+solid | area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.area.section+solid_id | area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.area.extra | area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cyl.area.section.goal_sid | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cyl.distance.segment+solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.solid | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.volume.solid_id | volume | solid_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.volume.both | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.notation | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.volume.conflict | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.section | volume | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.section+solid | volume | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.section+solid_id | volume | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.extra | volume | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.volume.section.goal_sid | volume | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.solid | lateral_area | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.lateral_area.solid_id | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.both | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.notation | lateral_area | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.lateral_area.conflict | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.section | lateral_area | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.section+solid | lateral_area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.section+solid_id | lateral_area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.extra | lateral_area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.lateral_area.section.goal_sid | lateral_area | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.solid | radius | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.radius.solid_id | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.both | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.notation | radius | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.radius.conflict | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.section | radius | section_id | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.radius.section+solid | radius | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.section+solid_id | radius | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.extra | radius | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.radius.section.goal_sid | radius | section_id | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.area.solid | area | solid | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.area.solid_id | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.area.both | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.area.notation | area | solid | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.area.conflict | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.area.section | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.area.section+solid | area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.area.section+solid_id | area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.area.extra | area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.cone.area.section.goal_sid | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.cone.distance.segment+solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.solid | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.volume.solid_id | volume | solid_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.volume.both | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.notation | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.volume.conflict | volume | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.section | volume | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.section+solid | volume | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.section+solid_id | volume | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.extra | volume | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.volume.section.goal_sid | volume | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.solid | lateral_area | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.lateral_area.solid_id | lateral_area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.both | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.notation | lateral_area | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.lateral_area.conflict | lateral_area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.section | lateral_area | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.section+solid | lateral_area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.section+solid_id | lateral_area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.extra | lateral_area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.lateral_area.section.goal_sid | lateral_area | section_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.solid | radius | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.radius.solid_id | radius | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.both | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.notation | radius | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.radius.conflict | radius | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.section | radius | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.radius.section+solid | radius | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.section+solid_id | radius | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.extra | radius | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.radius.section.goal_sid | radius | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.area.solid | area | solid | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.area.solid_id | area | solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.area.both | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.area.notation | area | solid | CONTROL | VALID | VALID | GEOMETRY_OPERAND_TYPE | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.area.conflict | area | solid, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.area.section | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.area.section+solid | area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.area.section+solid_id | area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.area.extra | area | solid, foo | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| K.sph.area.section.goal_sid | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_CURVED | BRIDGE_UNSUPPORTED_CURVED |
| K.sph.distance.segment+solid | distance | segment, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.demo1.area.section | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_CUT_EDGES_NOT_STATED | SOURCE_OBJECT_MISMATCH |
| S.demo1.area.section+solid | area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.demo1.area.section+solid_id | area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.demo1.area.section_unknown | area | section_id | CONTROL | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID |
| S.demo1.area.section_int | area | section_id | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.demo1.area.section.goal_sid | area | section_id | CONTROL | VALID | VALID | SERVED | BRIDGE_CUT_EDGES_NOT_STATED | SOURCE_OBJECT_MISMATCH |
| S.demo1.area.section.goal_sid_conflict | area | section_id | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| S.dev10.area.section | area | section_id | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| S.dev10.area.section+solid | area | section_id, solid | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.dev10.area.section+solid_id | area | section_id, solid_id | F1 | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.dev10.area.section_unknown | area | section_id | CONTROL | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID | UNKNOWN_SECTION_ID |
| S.dev10.area.section_int | area | section_id | CONTROL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL | INVALID_MATH_GOAL |
| S.dev10.area.section.goal_sid | area | section_id | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| S.dev10.area.section.goal_sid_conflict | area | section_id | CONTROL | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID | UNKNOWN_SOLID_ID |
| D.top.SM | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| D.top.SB | distance | segment | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| D.top.SA | distance | segment | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| D.top.MC | distance | segment | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| D.top.qualB | distance | segment | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| D.top.qualS | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| D.main.SB | distance | segment | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| D.main.qualtopS | distance | segment | CONTROL | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| D.top.M_plane_ABC | distance | point, plane | CONTROL | VALID | VALID | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
| D.top.vol | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| D.top.vol_id | volume | solid_id | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| D.top.vol_goal | volume | solid | CONTROL | VALID | VALID | SERVED | BRIDGE_UNSUPPORTED_RELATION | BRIDGE_UNSUPPORTED_RELATION |
| D.top.vol_conflict | volume | solid | CONTROL | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH | SOURCE_OBJECT_MISMATCH |
