---
id: "minmax8_8bit_001"
context.module: "MINMAX8"
context.data_width: 8
context.type: "8-bit min/max selector"
signals: ["a", "b", "min_o", "max_o"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the min/max selector for cases where the first operand is larger, the second is larger, and the two are equal, across low and high operand ranges.

## Notes
(none)

## RTL
```verilog
module minmax8(a, b, min_o, max_o);
  input [7:0] a, b;
  output [7:0] min_o, max_o;
  assign min_o = (a < b) ? a : b;
  assign max_o = (a < b) ? b : a;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_minmax (ref logic [7:0] a, b, min_o, max_o);
  a_cp : coverpoint a {
    bins low  = {[0:127]};
    bins high = {[128:255]};
  }
  b_cp : coverpoint b {
    bins low  = {[0:127]};
    bins high = {[128:255]};
  }
  a_x_b : cross a_cp, b_cp;
endgroup
```
