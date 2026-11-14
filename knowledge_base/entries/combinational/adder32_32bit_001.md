---
id: "adder32_32bit_001"
context.module: "ADDER32"
context.data_width: 32
context.type: "32-bit adder"
signals: ["a", "b", "sum", "cout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 32-bit adder behavior across low, mid, and high value ranges for both operands and the sum, including zero and maximum boundaries, and the overflow carry-out in both states.

## Notes
(none)

## RTL
```verilog
module adder32(a, b, sum, cout);
  input [31:0] a, b;
  output [31:0] sum;
  output cout;
  assign {cout, sum} = a + b;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_adder32 (ref logic [31:0] a, b, sum, ref logic cout);
  a_cp : coverpoint a {
    bins zero = {0};
    bins low  = {[1:32'h0000_FFFF]};
    bins high = {[32'h0001_0000:32'hFFFF_FFFE]};
    bins max  = {32'hFFFF_FFFF};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins low  = {[1:32'h0000_FFFF]};
    bins high = {[32'h0001_0000:32'hFFFF_FFFE]};
    bins max  = {32'hFFFF_FFFF};
  }
  sum_cp : coverpoint sum {
    bins zero = {0};
    bins mid  = {[1:32'hFFFF_FFFE]};
    bins max  = {32'hFFFF_FFFF};
  }
  cout_cp : coverpoint cout {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  a_x_b : cross a_cp, b_cp;
endgroup
```
