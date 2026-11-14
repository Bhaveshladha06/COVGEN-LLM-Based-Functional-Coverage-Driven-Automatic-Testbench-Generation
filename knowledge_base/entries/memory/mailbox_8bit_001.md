---
id: "mailbox_8bit_001"
context.module: "MAILBOX"
context.data_width: 8
context.type: "single-entry mailbox"
signals: ["clk", "rst_n", "put", "get", "din", "dout", "occupied"]
verified: false
provenance: "hand_authored"
category: "memory"
---

## Requirement
Cover the mailbox accepting a message when empty, rejecting a put while occupied, delivering on get, and the occupied flag transitioning in both directions.

## Notes
(none)

## RTL
```verilog
module mailbox(clk, rst_n, put, get, din, dout, occupied);
  input clk, rst_n, put, get;
  input [7:0] din;
  output reg [7:0] dout;
  output reg occupied;
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      occupied <= 1'b0;
      dout     <= 8'b0;
    end else if (put && !occupied) begin
      dout     <= din;
      occupied <= 1'b1;
    end else if (get && occupied) begin
      occupied <= 1'b0;
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_mailbox (ref logic put, get, occupied, ref logic [7:0] din) @(posedge clk);
  put_cp : coverpoint put {
    bins idle = {0};
    bins put  = {1};
  }
  get_cp : coverpoint get {
    bins idle = {0};
    bins get  = {1};
  }
  occ_cp : coverpoint occupied {
    bins empty_m    = {0};
    bins occupied_m = {1};
  }
  occ_trans_cp : coverpoint occupied {
    bins fill  = (0 => 1);
    bins drain = (1 => 0);
  }
  put_x_occ : cross put_cp, occ_cp;
  get_x_occ : cross get_cp, occ_cp;
  put_x_get : cross put_cp, get_cp;
endgroup
```
