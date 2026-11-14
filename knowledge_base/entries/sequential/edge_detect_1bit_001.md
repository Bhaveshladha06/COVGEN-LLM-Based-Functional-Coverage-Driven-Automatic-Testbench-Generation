---
id: "edge_detect_1bit_001"
context.module: "EDGE_DETECT"
context.data_width: 1
context.type: "edge detector"
signals: ["clk", "rst_n", "din", "rise", "fall"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the edge detector asserting the rising-edge pulse on a low-to-high input transition and the falling-edge pulse on a high-to-low transition, with neither asserted while the input is steady.

## Notes
(none)

## RTL
```verilog
module edge_detect(clk, rst_n, din, rise, fall);
  input clk, rst_n, din;
  output rise, fall;
  reg din_d;
  assign rise = din & ~din_d;
  assign fall = ~din & din_d;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) din_d <= 1'b0;
    else        din_d <= din;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_edge (ref logic din, rise, fall) @(posedge clk);
  din_cp : coverpoint din {
    bins low  = {0};
    bins high = {1};
  }
  pulse_cp : coverpoint {rise, fall} {
    bins steady  = {2'b00};
    bins falling = {2'b01};
    bins rising  = {2'b10};
    illegal_bins both = {2'b11};
  }
  din_trans_cp : coverpoint din {
    bins rise_edge = (0 => 1);
    bins fall_edge = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  din_x_pulse : cross din_cp, pulse_cp;
endgroup
```
