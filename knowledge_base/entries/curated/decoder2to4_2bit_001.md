---
id: "decoder2to4_2bit_001"
context.module: "DECODER2TO4"
context.data_width: 2
context.type: "2-to-4 decoder"
signals: ["sel", "y"]
verified: true
provenance: "curated_seed"
category: "curated"
---

## Requirement
Cover 2-to-4 decoder behavior for all select values and the corresponding one-hot output, treating non-one-hot outputs as illegal.

## Notes
(none)

## RTL
```verilog
module decoder2to4(sel, y);
  input [1:0] sel;
  output [3:0] y;

  assign y = 4'b0001 << sel;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_dec (ref logic [1:0] sel, ref logic [3:0] y);
  sel_cp: coverpoint sel {
    bins sel_0 = {2'b00};
    bins sel_1 = {2'b01};
    bins sel_2 = {2'b10};
    bins sel_3 = {2'b11};
  }

  y_cp: coverpoint y {
    bins onehot[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    illegal_bins invalid = default;
  }

  c_sel_y : cross sel_cp, y_cp {
    bins sel0_y1 = binsof(sel_cp.sel_0) && binsof(y_cp) intersect {4'b0001};
    bins sel1_y2 = binsof(sel_cp.sel_1) && binsof(y_cp) intersect {4'b0010};
    bins sel2_y4 = binsof(sel_cp.sel_2) && binsof(y_cp) intersect {4'b0100};
    bins sel3_y8 = binsof(sel_cp.sel_3) && binsof(y_cp) intersect {4'b1000};
  }
endgroup
```
