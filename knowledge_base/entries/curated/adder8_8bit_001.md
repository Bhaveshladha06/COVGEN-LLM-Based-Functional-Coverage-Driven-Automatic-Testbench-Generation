---
id: "adder8_8bit_001"
context.module: "ADDER8"
context.data_width: 8
context.type: "8-bit adder"
signals: ["a", "b", "sum"]
verified: true
provenance: "curated_seed"
category: "curated"
---

## Requirement
Cover 8-bit adder behavior across low, mid, and high value ranges for inputs a, b and resulting sum, including boundary and overflow conditions.

## Notes
(none)

## RTL
```verilog
module adder8(a, b, sum);
  input [7:0] a, b;
  output [7:0] sum;

  assign sum = a + b;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_adder8 (ref logic [7:0] a, b, sum);

  cp_a: coverpoint a {
    bins low  = {[0:10]};
    bins mid  = {[11:244]};
    bins high = {[245:255]};
  }

  cp_b: coverpoint b {
    bins low  = {[0:10]};
    bins mid  = {[11:244]};
    bins high = {[245:255]};
  }

  cp_sum: coverpoint sum {
    bins zero = {0};
    bins max  = {255};
    bins mid  = {[1:254]};
  }

  cp_a_b_sum: cross cp_a, cp_b, cp_sum;

endgroup
```
