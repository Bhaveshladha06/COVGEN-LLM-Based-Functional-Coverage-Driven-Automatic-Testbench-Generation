---
id: "arbiter_fixed_4bit_001"
context.module: "ARBITER_FIXED"
context.data_width: 4
context.type: "fixed priority arbiter"
signals: ["clk", "rst_n", "req", "grant"]
verified: false
provenance: "hand_authored"
category: "control"
---

## Requirement
Cover the fixed priority arbiter granting each requester, the no-request idle case, simultaneous requests resolving to the highest priority, and confirm the grant is always one-hot or zero.

## Notes
(none)

## RTL
```verilog
module arbiter_fixed(clk, rst_n, req, grant);
  input clk, rst_n;
  input [3:0] req;
  output reg [3:0] grant;
  always @(*) begin
    casex (req)
      4'bxxx1: grant = 4'b0001;
      4'bxx10: grant = 4'b0010;
      4'bx100: grant = 4'b0100;
      4'b1000: grant = 4'b1000;
      default: grant = 4'b0000;
    endcase
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_arb_fixed (ref logic [3:0] req, grant);
  req_cp : coverpoint req {
    bins none      = {4'b0000};
    bins single[]  = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    bins multiple  = {[4'b0011:4'b0111], [4'b1001:4'b1111]};
  }
  grant_cp : coverpoint grant {
    bins idle     = {4'b0000};
    bins onehot[] = {4'b0001, 4'b0010, 4'b0100, 4'b1000};
    illegal_bins multi_grant = default;
  }
  req_x_grant : cross req_cp, grant_cp;
endgroup
```
