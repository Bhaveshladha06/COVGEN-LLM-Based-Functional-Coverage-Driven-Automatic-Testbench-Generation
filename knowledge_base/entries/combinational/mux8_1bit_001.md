---
id: "mux8_1bit_001"
context.module: "MUX8"
context.data_width: 8
context.type: "8-to-1 multiplexer"
signals: ["d", "sel", "y"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-to-1 multiplexer behavior for every select value, toggling of each data input bit, and the output value observed for each select.

## Notes
(none)

## RTL
```verilog
module mux8(d, sel, y);
  input [7:0] d;
  input [2:0] sel;
  output y;
  assign y = d[sel];
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mux8 (ref logic [7:0] d, ref logic [2:0] sel, ref logic y);
  sel_cp : coverpoint sel {
    bins s[] = {[0:7]};
  }
  y_cp : coverpoint y {
    bins y_0 = {0};
    bins y_1 = {1};
  }
  sel_x_y : cross sel_cp, y_cp;
endgroup
```
