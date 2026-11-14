---
id: "mux4_1bit_001"
context.module: "MUX4"
context.data_width: 4
context.type: "4-to-1 multiplexer"
signals: ["d", "sel", "y"]
verified: true
provenance: "curated_seed"
category: "curated"
---

## Requirement
Cover 4-to-1 multiplexer behavior for all select values, input bit toggling, and output value per select combination.

## Notes
(none)

## RTL
```verilog
module mux4(d, sel, y);
  input [3:0] d;
  input [1:0] sel;
  output reg y;

  always @(*) begin
    case(sel)
      2'b00: y = d[0];
      2'b01: y = d[1];
      2'b10: y = d[2];
      2'b11: y = d[3];
    endcase
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mux4 (ref logic [3:0] d, ref logic [1:0] sel, ref logic y);

  sel_cp : coverpoint sel {
    bins sel_0 = {2'b00};
    bins sel_1 = {2'b01};
    bins sel_2 = {2'b10};
    bins sel_3 = {2'b11};
  }

  // toggle-style coverage: did each input bit ever see 0 and 1?
  d0_cp : coverpoint d[0];
  d1_cp : coverpoint d[1];
  d2_cp : coverpoint d[2];
  d3_cp : coverpoint d[3];

  // functional coverage: for each sel, did y see both values?
  y_cp : coverpoint y {
    bins y_0 = {0};
    bins y_1 = {1};
  }

  sel_x_y : cross sel_cp, y_cp;   // 4 x 2 = 8 meaningful bins

endgroup
```
