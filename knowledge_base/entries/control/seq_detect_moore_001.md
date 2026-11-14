---
id: "seq_detect_moore_001"
context.module: "SEQ_DETECT_MOORE"
context.data_width: 3
context.type: "sequence detector 1011 (Moore)"
signals: ["clk", "rst_n", "din", "state", "detected"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the Moore sequence detector visiting every state, detecting the target pattern, the overlapping detection case, and returning to the idle state on a mismatching bit.

## Notes
(none)

## RTL
```verilog
module seq_detect_moore(clk, rst_n, din, state, detected);
  input clk, rst_n, din;
  output reg [2:0] state;
  output detected;
  parameter S0=3'd0, S1=3'd1, S10=3'd2, S101=3'd3, S1011=3'd4;
  assign detected = (state == S1011);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S0;
    else begin
      case (state)
        S0:    state <= din ? S1   : S0;
        S1:    state <= din ? S1   : S10;
        S10:   state <= din ? S101 : S0;
        S101:  state <= din ? S1011: S10;
        S1011: state <= din ? S1   : S10;
        default: state <= S0;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_seq_moore (ref logic [2:0] state, ref logic din, detected) @(posedge clk);
  state_cp : coverpoint state {
    bins s0    = {3'd0};
    bins s1    = {3'd1};
    bins s10   = {3'd2};
    bins s101  = {3'd3};
    bins s1011 = {3'd4};
    illegal_bins unused = {[3'd5:3'd7]};
  }
  din_cp : coverpoint din {
    bins zero = {0};
    bins one  = {1};
  }
  detected_cp : coverpoint detected {
    bins no_match = {0};
    bins match    = {1};
  }
  state_trans_cp : coverpoint state {
    bins to_match   = (3'd3 => 3'd4);
    bins overlap    = (3'd4 => 3'd1);
    bins restart    = (3'd2 => 3'd0);
  }
  state_x_din : cross state_cp, din_cp;
endgroup
```
