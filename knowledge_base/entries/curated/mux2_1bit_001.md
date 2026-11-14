---
id: "mux2_1bit_001"
context.module: "MUX2"
context.data_width: 1
context.type: "2-to-1 multiplexer"
signals: ["a", "b", "sel", "y"]
verified: true
provenance: "curated_seed"
category: "curated"
---

## Requirement
Cover 2-to-1 multiplexer behavior for all combinations of select and input values.

## Notes
(none)

## RTL
```verilog
module mux2(a, b, sel, y);
  input a, b, sel;
  output y;
  assign y = sel ? b : a;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mux2 (ref logic a, b, sel);
  sel_cp : coverpoint sel {
    bins sel_0 = {0};
    bins sel_1 = {1};
  }

  ab_cp : coverpoint {a, b} {
    bins ab_00 = {2'b00};
    bins ab_01 = {2'b01};
    bins ab_10 = {2'b10};
    bins ab_11 = {2'b11};
  }

  sel_x_ab : cross sel_cp, ab_cp;
endgroup
```
