---
id: "comparator8_8bit_001"
context.module: "COMPARATOR8"
context.data_width: 8
context.type: "8-bit magnitude comparator"
signals: ["a", "b", "gt", "eq", "lt"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-bit comparator behavior for the greater-than, equal, and less-than outputs, ensuring each is asserted at least once and that exactly one is active per comparison.

## Notes
(none)

## RTL
```verilog
module comparator8(a, b, gt, eq, lt);
  input [7:0] a, b;
  output gt, eq, lt;
  assign gt = (a > b);
  assign eq = (a == b);
  assign lt = (a < b);
endmodule
```

## Coverage model
```systemverilog
covergroup cg_cmp8 (ref logic [7:0] a, b, ref logic gt, eq, lt);
  a_cp : coverpoint a {
    bins low  = {[0:84]};
    bins mid  = {[85:169]};
    bins high = {[170:255]};
  }
  b_cp : coverpoint b {
    bins low  = {[0:84]};
    bins mid  = {[85:169]};
    bins high = {[170:255]};
  }
  result_cp : coverpoint {gt, eq, lt} {
    bins is_gt = {3'b100};
    bins is_eq = {3'b010};
    bins is_lt = {3'b001};
    illegal_bins impossible = default;
  }
  a_x_b : cross a_cp, b_cp;
endgroup
```
