---
id: "bcd_adder_4bit_001"
context.module: "BCD_ADDER"
context.data_width: 4
context.type: "BCD adder"
signals: ["a", "b", "cin", "sum", "cout"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover BCD adder behavior for all valid decimal digit operands, both carry-in states, the carry-out generated when the result exceeds nine, and treat non-decimal operand values as illegal.

## Notes
(none)

## RTL
```verilog
module bcd_adder(a, b, cin, sum, cout);
  input [3:0] a, b;
  input cin;
  output reg [3:0] sum;
  output reg cout;
  reg [4:0] tmp;
  always @(*) begin
    tmp = a + b + cin;
    if (tmp > 9) begin
      sum  = tmp - 10;
      cout = 1'b1;
    end else begin
      sum  = tmp[3:0];
      cout = 1'b0;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_bcd_add (ref logic [3:0] a, b, sum, ref logic cin, cout);
  a_cp : coverpoint a {
    bins digit[] = {[0:9]};
    illegal_bins non_bcd = {[10:15]};
  }
  b_cp : coverpoint b {
    bins digit[] = {[0:9]};
    illegal_bins non_bcd = {[10:15]};
  }
  cin_cp : coverpoint cin {
    bins no_carry = {0};
    bins carry    = {1};
  }
  cout_cp : coverpoint cout {
    bins no_carry = {0};
    bins carry    = {1};
  }
  a_x_b     : cross a_cp, b_cp;
  cin_x_cout: cross cin_cp, cout_cp;
endgroup
```
