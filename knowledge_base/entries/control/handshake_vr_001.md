---
id: "handshake_vr_001"
context.module: "HANDSHAKE_VR"
context.data_width: 8
context.type: "valid-ready handshake"
signals: ["clk", "rst_n", "valid", "ready", "data", "xfer"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the valid-ready handshake for all four combinations of valid and ready, the transfer occurring only when both are asserted, valid waiting for ready, and back-to-back transfers.

## Notes
(none)

## RTL
```verilog
module handshake_vr(clk, rst_n, valid, ready, data, xfer);
  input clk, rst_n, valid, ready;
  input [7:0] data;
  output xfer;
  assign xfer = valid && ready;
endmodule
```

## Coverage model
```systemverilog
covergroup cg_handshake (ref logic valid, ready, xfer, ref logic [7:0] data) @(posedge clk);
  vr_cp : coverpoint {valid, ready} {
    bins idle        = {2'b00};
    bins ready_only  = {2'b01};
    bins valid_wait  = {2'b10};
    bins transfer    = {2'b11};
  }
  xfer_cp : coverpoint xfer {
    bins no_xfer = {0};
    bins xfer    = {1};
  }
  xfer_trans_cp : coverpoint xfer {
    bins back_to_back = (1 => 1);
    bins start        = (0 => 1);
    bins stop         = (1 => 0);
  }
  data_cp : coverpoint data {
    bins zero = {8'h00};
    bins mid  = {[8'h01:8'hFE]};
    bins max  = {8'hFF};
  }
  vr_x_data : cross vr_cp, data_cp;
endgroup
```
