---
id: "mux2_en_1bit_001"
context.module: "MUX2_EN"
context.data_width: 1
context.type: "2-to-1 multiplexer with enable"
signals: ["a", "b", "sel", "en", "y"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover the enabled 2-to-1 multiplexer for both select values and all data input combinations while enabled, and the forced-zero output while disabled.

## Notes
(none)

## RTL
```verilog
module mux2_en(a, b, sel, en, y);
  input a, b, sel, en;
  output y;
  assign y = en ? (sel ? b : a) : 1'b0;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mux2_en (ref logic a, b, sel, en, y);
  sel_cp : coverpoint sel {
    bins sel_a = {0};
    bins sel_b = {1};
  }
  en_cp : coverpoint en {
    bins disabled = {0};
    bins enabled  = {1};
  }
  ab_cp : coverpoint {a, b} {
    bins ab[] = {[2'b00:2'b11]};
  }
  sel_x_en : cross sel_cp, en_cp;
  ab_x_sel : cross ab_cp, sel_cp;
endgroup
```
