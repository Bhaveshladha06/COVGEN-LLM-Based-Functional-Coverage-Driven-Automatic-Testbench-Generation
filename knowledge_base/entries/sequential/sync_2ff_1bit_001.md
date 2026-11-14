---
id: "sync_2ff_1bit_001"
context.module: "SYNC_2FF"
context.data_width: 1
context.type: "two flip-flop synchronizer"
signals: ["clk", "rst_n", "async_in", "sync_out"]
verified: false
provenance: "hand_authored"
category: "sequential"
---

## Requirement
Cover the two-stage synchronizer propagating both input values through to the output, and both output transition directions after the synchronization delay.

## Notes
(none)

## RTL
```verilog
module sync_2ff(clk, rst_n, async_in, sync_out);
  input clk, rst_n, async_in;
  output sync_out;
  reg s1, s2;
  assign sync_out = s2;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      s1 <= 1'b0;
      s2 <= 1'b0;
    end else begin
      s1 <= async_in;
      s2 <= s1;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_sync2ff (ref logic async_in, sync_out) @(posedge clk);
  in_cp : coverpoint async_in {
    bins low  = {0};
    bins high = {1};
  }
  out_cp : coverpoint sync_out {
    bins low  = {0};
    bins high = {1};
  }
  out_trans_cp : coverpoint sync_out {
    bins rise = (0 => 1);
    bins fall = (1 => 0);
  }
  in_x_out : cross in_cp, out_cp;
endgroup
```
