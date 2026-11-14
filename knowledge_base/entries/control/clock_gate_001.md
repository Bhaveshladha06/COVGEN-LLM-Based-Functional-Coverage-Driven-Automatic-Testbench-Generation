---
id: "clock_gate_001"
context.module: "CLOCK_GATE"
context.data_width: 1
context.type: "glitch-free clock gate"
signals: ["clk", "rst_n", "enable", "gated_clk", "latched_en"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the clock gate enabling and disabling the gated output, the enable being latched on the correct clock phase, and both transition directions of the latched enable.

## Notes
(none)

## RTL
```verilog
module clock_gate(clk, rst_n, enable, gated_clk, latched_en);
  input clk, rst_n, enable;
  output gated_clk;
  output reg latched_en;
  assign gated_clk = clk & latched_en;
  always @(negedge clk or negedge rst_n) begin
    if (!rst_n) latched_en <= 1'b0;
    else        latched_en <= enable;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_clkgate (ref logic enable, latched_en) @(posedge clk);
  enable_cp : coverpoint enable {
    bins off = {0};
    bins on  = {1};
  }
  latched_cp : coverpoint latched_en {
    bins gated   = {0};
    bins passing = {1};
  }
  latched_trans_cp : coverpoint latched_en {
    bins turn_on  = (0 => 1);
    bins turn_off = (1 => 0);
    bins stay_off = (0 => 0);
    bins stay_on  = (1 => 1);
  }
  enable_x_latched : cross enable_cp, latched_cp;
endgroup
```
