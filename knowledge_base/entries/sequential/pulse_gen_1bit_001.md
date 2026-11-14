---
id: "pulse_gen_1bit_001"
context.module: "PULSE_GEN"
context.data_width: 1
context.type: "single-cycle pulse generator"
signals: ["clk", "rst_n", "trig", "pulse"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the pulse generator emitting exactly one cycle of output pulse per trigger assertion, remaining low while the trigger is held, and rearming after the trigger is released.

## Notes
(none)

## RTL
```verilog
module pulse_gen(clk, rst_n, trig, pulse);
  input clk, rst_n, trig;
  output pulse;
  reg trig_d;
  assign pulse = trig & ~trig_d;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) trig_d <= 1'b0;
    else        trig_d <= trig;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_pulse (ref logic trig, pulse) @(posedge clk);
  trig_cp : coverpoint trig {
    bins idle    = {0};
    bins asserted= {1};
  }
  pulse_cp : coverpoint pulse {
    bins low  = {0};
    bins high = {1};
  }
  pulse_trans_cp : coverpoint pulse {
    bins fire   = (0 => 1);
    bins retire = (1 => 0);
  }
  trig_x_pulse : cross trig_cp, pulse_cp;
endgroup
```
