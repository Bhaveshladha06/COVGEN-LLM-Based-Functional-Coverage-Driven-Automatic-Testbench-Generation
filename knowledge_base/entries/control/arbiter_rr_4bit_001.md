---
id: "arbiter_rr_4bit_001"
context.module: "ARBITER_RR"
context.data_width: 4
context.type: "round-robin arbiter"
signals: ["clk", "rst_n", "req", "grant", "last_grant"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the round-robin arbiter granting every requester in turn, rotating priority after each grant, handling simultaneous requests fairly, and the idle case with no requests.

## Notes
(none)

## RTL
```verilog
module arbiter_rr(clk, rst_n, req, grant, last_grant);
  input clk, rst_n;
  input [3:0] req;
  output reg [3:0] grant;
  output reg [1:0] last_grant;
  integer i;
  always @(*) begin
    grant = 4'b0000;
    for (i = 0; i < 4; i = i + 1) begin
      if (grant == 4'b0000 && req[(last_grant + 1 + i) % 4])
        grant[(last_grant + 1 + i) % 4] = 1'b1;
    end
  end
  always @(posedge clk or negedge rst_n) begin
    if (!rst_n) last_grant <= 2'd0;
    else if (grant != 4'b0000) begin
      case (grant)
        4'b0001: last_grant <= 2'd0;
        4'b0010: last_grant <= 2'd1;
        4'b0100: last_grant <= 2'd2;
        4'b1000: last_grant <= 2'd3;
        default: last_grant <= last_grant;
      endcase
    end
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_arb_rr (ref logic [3:0] req, grant, ref logic [1:0] last_grant) @(posedge clk);
  req_cp : coverpoint req {
    bins none     = {4'b0000};
    bins single[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    bins all_req  = {4'b1111};
    bins multiple = {[4'b0011:4'b0111], [4'b1001:4'b1110]};
  }
  grant_cp : coverpoint grant {
    bins idle     = {4'b0000};
    bins onehot[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
  }
  last_cp : coverpoint last_grant {
    bins owner[] = {[0:3]};
  }
  last_trans_cp : coverpoint last_grant {
    bins rotate_0_1 = (2'd0 => 2'd1);
    bins rotate_1_2 = (2'd1 => 2'd2);
    bins rotate_2_3 = (2'd2 => 2'd3);
    bins rotate_3_0 = (2'd3 => 2'd0);
  }
  req_x_grant  : cross req_cp, grant_cp;
  last_x_grant : cross last_cp, grant_cp;
endgroup
```
