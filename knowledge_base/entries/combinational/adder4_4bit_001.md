---
id: "adder4_4bit_001"
context.module: "ADDER4"
context.data_width: 4
context.type: "4-bit adder with carry"
signals: ["a", "b", "cin", "sum", "cout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 4-bit adder behavior across the full input range for both operands, both carry-in states, and the carry-out asserted and deasserted, crossing carry-in against carry-out.

## Notes
(none)

## RTL
```verilog
module adder4(a, b, cin, sum, cout);
  input [3:0] a, b;
  input cin;
  output [3:0] sum;
  output cout;
  assign {cout, sum} = a + b + cin;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_adder4 (ref logic [3:0] a, b, sum, ref logic cin, cout);
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  cin_cp : coverpoint cin {
    bins no_carry = {0};
    bins carry    = {1};
  }
  cout_cp : coverpoint cout {
    bins no_ovf = {0};
    bins ovf    = {1};
  }
  a_x_b     : cross a_cp, b_cp;
  cin_x_cout: cross cin_cp, cout_cp;
endgroup
```
