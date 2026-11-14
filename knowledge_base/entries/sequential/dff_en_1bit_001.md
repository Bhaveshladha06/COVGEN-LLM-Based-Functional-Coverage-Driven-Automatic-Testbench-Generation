---
id: "dff_en_1bit_001"
context.module: "DFF_EN"
context.data_width: 1
context.type: "D flip-flop with clock enable"
signals: ["clk", "rst_n", "en", "d", "q"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the enabled D flip-flop loading new data when the enable is asserted, holding its value when the enable is deasserted, and the cross of enable against data.

## Notes
(none)

## RTL
```verilog
module dff_en(clk, rst_n, en, d, q);
  input clk, rst_n, en, d;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)   q <= 1'b0;
    else if (en)  q <= d;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_dff_en (ref logic d, q, en) @(posedge clk);
  en_cp : coverpoint en {
    bins hold = {0};
    bins load = {1};
  }
  d_cp : coverpoint d {
    bins low  = {0};
    bins high = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise      = (0 => 1);
    bins fall      = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  en_x_d : cross en_cp, d_cp;
endgroup
```
