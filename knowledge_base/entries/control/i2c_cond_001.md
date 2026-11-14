---
id: "i2c_cond_001"
context.module: "I2C_COND"
context.data_width: 1
context.type: "I2C start/stop condition detector"
signals: ["clk", "rst_n", "scl", "sda", "start_cond", "stop_cond"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the I2C condition detector recognising a start condition when data falls while clock is high, a stop condition when data rises while clock is high, and neither during normal data transitions.

## Notes
(none)

## RTL
```verilog
module i2c_cond(clk, rst_n, scl, sda, start_cond, stop_cond);
  input clk, rst_n, scl, sda;
  output start_cond, stop_cond;
  reg sda_d;
  assign start_cond = scl && sda_d && !sda;
  assign stop_cond  = scl && !sda_d && sda;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) sda_d <= 1'b1;
    else        sda_d <= sda;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_i2c_cond (ref logic scl, sda, start_cond, stop_cond) @(posedge clk);
  bus_cp : coverpoint {scl, sda} {
    bins both_low  = {2'b00};
    bins clk_low   = {2'b01};
    bins data_low  = {2'b10};
    bins both_high = {2'b11};
  }
  cond_cp : coverpoint {start_cond, stop_cond} {
    bins none  = {2'b00};
    bins stop  = {2'b01};
    bins start = {2'b10};
    illegal_bins both = {2'b11};
  }
  sda_trans_cp : coverpoint sda {
    bins fall = (1 => 0);
    bins rise = (0 => 1);
  }
  bus_x_cond : cross bus_cp, cond_cp;
endgroup
```
