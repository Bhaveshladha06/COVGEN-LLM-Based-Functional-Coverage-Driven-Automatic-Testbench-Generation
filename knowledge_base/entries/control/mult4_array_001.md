---
id: "mult4_array_001"
context.module: "MULT4"
context.data_width: 4
context.type: "4-bit array multiplier"
signals: ["a", "b", "product"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the 4-bit array multiplier for zero, unity, and maximum operands, the full product range including the maximum product, and the cross of the two operand ranges.

## Notes
(none)

## RTL
```verilog
module mult4(a, b, product);
  input [3:0] a, b;
  output [7:0] product;
  assign product = a * b;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mult4 (ref logic [3:0] a, b, ref logic [7:0] product);
  a_cp : coverpoint a {
    bins zero = {0};
    bins one  = {1};
    bins mid  = {[2:14]};
    bins max  = {15};
  }
  b_cp : coverpoint b {
    bins zero = {0};
    bins one  = {1};
    bins mid  = {[2:14]};
    bins max  = {15};
  }
  product_cp : coverpoint product {
    bins zero = {0};
    bins low  = {[1:63]};
    bins high = {[64:224]};
    bins max  = {225};
  }
  a_x_b : cross a_cp, b_cp;
endgroup
```
