---
id: "seq_detect_mealy_001"
context.module: "SEQ_DETECT_MEALY"
context.data_width: 2
context.type: "sequence detector 110 (Mealy)"
signals: ["clk", "rst_n", "din", "state", "detected"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the Mealy sequence detector across all states, the detection output asserting combinationally on the final input bit, and each state transition taken for both input values.

## Notes
(none)

## RTL
```verilog
module seq_detect_mealy(clk, rst_n, din, state, detected);
  input clk, rst_n, din;
  output reg [1:0] state;
  output detected;
  parameter S0=2'd0, S1=2'd1, S11=2'd2;
  assign detected = (state == S11) && (din == 1'b0);
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= S0;
    else begin
      case (state)
        S0:  state <= din ? S1  : S0;
        S1:  state <= din ? S11 : S0;
        S11: state <= din ? S11 : S0;
        default: state <= S0;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_seq_mealy (ref logic [1:0] state, ref logic din, detected) @(posedge clk);
  state_cp : coverpoint state {
    bins s0  = {2'd0};
    bins s1  = {2'd1};
    bins s11 = {2'd2};
    illegal_bins unused = {2'd3};
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
    bins build1 = (2'd0 => 2'd1);
    bins build2 = (2'd1 => 2'd2);
    bins fire   = (2'd2 => 2'd0);
  }
  state_x_din : cross state_cp, din_cp;
endgroup
```
