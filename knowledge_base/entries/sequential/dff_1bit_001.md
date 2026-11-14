---
id: "dff_1bit_001"
context.module: "DFF"
context.data_width: 1
context.type: "D flip-flop with async reset"
signals: ["clk", "rst_n", "d", "q"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the D flip-flop capturing both data values on the clock edge, the asynchronous reset forcing the output low, and the transition of the output in both directions.

## Notes
(none)

## RTL
```verilog
module dff(clk, rst_n, d, q);
  input clk, rst_n, d;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else        q <= d;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_dff (ref logic d, q, rst_n) @(posedge clk);
  d_cp : coverpoint d {
    bins low  = {0};
    bins high = {1};
  }
  q_cp : coverpoint q {
    bins low  = {0};
    bins high = {1};
  }
  rst_cp : coverpoint rst_n {
    bins in_reset  = {0};
    bins out_reset = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  d_x_rst : cross d_cp, rst_cp;
endgroup
```
