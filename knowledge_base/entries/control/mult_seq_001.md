---
id: "mult_seq_001"
context.module: "MULT_SEQ"
context.data_width: 8
context.type: "sequential shift-add multiplier"
signals: ["clk", "rst_n", "start", "a", "b", "product", "done", "bitcnt"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the sequential multiplier through every iteration of its shift-add loop, the start and done handshake, zero and maximum operands, and the multiplier bit determining whether an add occurs.

## Notes
(none)

## RTL
```verilog
module mult_seq(clk, rst_n, start, a, b, product, done, bitcnt);
  input clk, rst_n, start;
  input [3:0] a, b;
  output reg [7:0] product;
  output done;
  output reg [2:0] bitcnt;
  reg [3:0] mplier;
  reg running;
  assign done = !running && (bitcnt == 3'd4);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      product <= 8'b0; bitcnt <= 3'd0; running <= 1'b0;
    end else if (start && !running) begin
      product <= 8'b0; mplier <= b; bitcnt <= 3'd0; running <= 1'b1;
    end else if (running) begin
      if (mplier[0]) product <= product + (a << bitcnt);
      mplier <= mplier >> 1;
      if (bitcnt == 3'd3) running <= 1'b0;
      bitcnt <= bitcnt + 1'b1;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mult_seq (ref logic [2:0] bitcnt, ref logic [3:0] a, b, ref logic start, done, running) @(posedge clk);
  bitcnt_cp : coverpoint bitcnt {
    bins iter[] = {[0:4]};
    illegal_bins overflow = {[5:7]};
  }
  a_cp : coverpoint a {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }
  running_cp : coverpoint running {
    bins idle    = {0};
    bins running = {1};
  }
  done_cp : coverpoint done {
    bins not_done = {0};
    bins done     = {1};
  }
  bitcnt_trans_cp : coverpoint bitcnt {
    bins step   = (0 => 1);
    bins finish = (3 => 4);
  }
  bitcnt_x_running : cross bitcnt_cp, running_cp;
  a_x_done         : cross a_cp, done_cp;
endgroup
```
