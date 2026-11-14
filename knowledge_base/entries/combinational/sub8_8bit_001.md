---
id: "sub8_8bit_001"
context.module: "SUB8"
context.data_width: 8
context.type: "8-bit subtractor"
signals: ["a", "b", "diff", "borrow"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-bit subtractor behavior for operand ranges, the zero and maximum difference values, and the borrow output asserted when the subtrahend exceeds the minuend.

## Notes
(none)

## RTL
```verilog
module sub8(a, b, diff, borrow);
  input [7:0] a, b;
  output [7:0] diff;
  output borrow;
  assign {borrow, diff} = a - b;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_sub8 (ref logic [7:0] a, b, diff, ref logic borrow);
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  diff_cp : coverpoint diff {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  borrow_cp : coverpoint borrow {
    bins no_borrow = {0};
    bins borrowed  = {1};
  }
  a_x_borrow : cross a_cp, borrow_cp;
endgroup
```
