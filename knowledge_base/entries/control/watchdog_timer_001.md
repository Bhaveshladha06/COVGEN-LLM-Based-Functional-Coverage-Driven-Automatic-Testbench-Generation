---
id: "watchdog_timer_001"
context.module: "WATCHDOG"
context.data_width: 8
context.type: "watchdog timer"
signals: ["clk", "rst_n", "kick", "timeout", "counter"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the watchdog timer counting up towards its limit, being kicked before expiry to reload the counter, expiring and asserting the timeout, and the counter spanning its range.

## Notes
(none)

## RTL
```verilog
module watchdog(clk, rst_n, kick, timeout, counter);
  input clk, rst_n, kick;
  output timeout;
  output reg [7:0] counter;
  assign timeout = (counter == 8'hFF);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n)        counter <= 8'b0;
    else if (kick)     counter <= 8'b0;
    else if (!timeout) counter <= counter + 1'b1;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_watchdog (ref logic [7:0] counter, ref logic kick, timeout) @(posedge clk);
  counter_cp : coverpoint counter {
    bins reloaded = {8'h00};
    bins early    = {[8'h01:8'h7F]};
    bins late     = {[8'h80:8'hFE]};
    bins expired  = {8'hFF};
  }
  kick_cp : coverpoint kick {
    bins idle = {0};
    bins kick = {1};
  }
  timeout_cp : coverpoint timeout {
    bins running = {0};
    bins expired = {1};
  }
  counter_trans_cp : coverpoint counter {
    bins reload_from_late = (8'h80 => 8'h00);
    bins reach_limit      = (8'hFE => 8'hFF);
  }
  kick_x_counter : cross kick_cp, counter_cp;
  kick_x_timeout : cross kick_cp, timeout_cp;
endgroup
```
