---
id: "crossbar2x2_001"
context.module: "CROSSBAR2X2"
context.data_width: 2
context.type: "2x2 crossbar switch"
signals: ["in0", "in1", "swap", "out0", "out1"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the 2x2 crossbar for both the pass-through and swapped configurations across all input combinations, crossing the swap control against the input pattern.

## Notes
(none)

## RTL
```verilog
module crossbar2x2(in0, in1, swap, out0, out1);
  input [1:0] in0, in1;
  input swap;
  output [1:0] out0, out1;
  assign out0 = swap ? in1 : in0;
  assign out1 = swap ? in0 : in1;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_xbar (ref logic [1:0] in0, in1, out0, out1, ref logic swap);
  swap_cp : coverpoint swap {
    bins pass    = {0};
    bins swapped = {1};
  }
  in0_cp : coverpoint in0 {
    bins v[] = {[0:3]};
  }
  in1_cp : coverpoint in1 {
    bins v[] = {[0:3]};
  }
  swap_x_in0 : cross swap_cp, in0_cp;
endgroup
```
