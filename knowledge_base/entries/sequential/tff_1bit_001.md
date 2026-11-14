---
id: "tff_1bit_001"
context.module: "TFF"
context.data_width: 1
context.type: "T flip-flop"
signals: ["clk", "rst_n", "t", "q"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the T flip-flop toggling its output when the toggle input is asserted, holding when deasserted, and both output transition directions.

## Notes
(none)

## RTL
```verilog
module tff(clk, rst_n, t, q);
  input clk, rst_n, t;
  output reg q;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= 1'b0;
    else if (t) q <= ~q;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_tff (ref logic t, q) @(posedge clk);
  t_cp : coverpoint t {
    bins hold   = {0};
    bins toggle = {1};
  }
  q_trans_cp : coverpoint q {
    bins rise      = (0 => 1);
    bins fall      = (1 => 0);
    bins hold_low  = (0 => 0);
    bins hold_high = (1 => 1);
  }
  q_cp : coverpoint q {
    bins low  = {0};
    bins high = {1};
  }
  t_x_q : cross t_cp, q_cp;
endgroup
```
