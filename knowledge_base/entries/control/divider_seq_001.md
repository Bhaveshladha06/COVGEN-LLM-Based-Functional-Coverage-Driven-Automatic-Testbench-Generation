---
id: "divider_seq_001"
context.module: "DIVIDER_SEQ"
context.data_width: 8
context.type: "sequential restoring divider"
signals: ["clk", "rst_n", "start", "dividend", "divisor", "quotient", "remainder", "done", "div_zero"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the sequential divider producing quotients across the value range, a zero remainder for exact division, the divide-by-zero error flag, and the done handshake completing each operation.

## Notes
(none)

## RTL
```verilog
module divider_seq(clk, rst_n, start, dividend, divisor, quotient, remainder, done, div_zero);
  input clk, rst_n, start;
  input [7:0] dividend, divisor;
  output reg [7:0] quotient, remainder;
  output reg done;
  output div_zero;
  reg [3:0] cnt;
  reg running;
  assign div_zero = (divisor == 8'b0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      quotient <= 0; remainder <= 0; done <= 0; cnt <= 0; running <= 0;
    end else if (start && !running && !div_zero) begin
      quotient <= dividend / divisor;
      remainder<= dividend % divisor;
      running  <= 1'b1; cnt <= 4'd0; done <= 1'b0;
    end else if (running) begin
      if (cnt == 4'd7) begin running <= 1'b0; done <= 1'b1; end
      else cnt <= cnt + 1'b1;
    end else done <= 1'b0;
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_divider (ref logic [7:0] dividend, divisor, quotient, remainder, ref logic done, div_zero) @(posedge clk);
  divisor_cp : coverpoint divisor {
    bins zero = {0};
    bins one  = {1};
    bins mid  = {[2:254]};
    bins max  = {255};
  }
  dividend_cp : coverpoint dividend {
    bins zero = {0};
    bins mid  = {[1:254]};
    bins max  = {255};
  }
  remainder_cp : coverpoint remainder {
    bins exact     = {0};
    bins non_exact = {[1:255]};
  }
  div_zero_cp : coverpoint div_zero {
    bins ok    = {0};
    bins error = {1};
  }
  done_cp : coverpoint done {
    bins busy = {0};
    bins done = {1};
  }
  divisor_x_rem : cross divisor_cp, remainder_cp;
  dividend_x_divisor : cross dividend_cp, divisor_cp;
endgroup
```
