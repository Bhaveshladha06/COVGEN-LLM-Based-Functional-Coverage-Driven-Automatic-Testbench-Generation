---
id: "encoder8to3_8bit_001"
context.module: "ENCODER8TO3"
context.data_width: 8
context.type: "8-to-3 binary encoder"
signals: ["d", "y", "valid"]
verified: false
provenance: "hand_authored"
category: "combinational"
---

## Requirement
Cover 8-to-3 encoder behavior for each one-hot input, the encoded output value for each, and the valid flag in both asserted and deasserted states.

## Notes
(none)

## RTL
```verilog
module encoder8to3(d, y, valid);
  input [7:0] d;
  output reg [2:0] y;
  output valid;
  assign valid = |d;
  always @(*) begin
    case (d)
      8'h01: y = 3'd0;
      8'h02: y = 3'd1;
      8'h04: y = 3'd2;
      8'h08: y = 3'd3;
      8'h10: y = 3'd4;
      8'h20: y = 3'd5;
      8'h40: y = 3'd6;
      8'h80: y = 3'd7;
      default: y = 3'd0;
    endcase
  end
endmodule
```

## Coverage model
```systemverilog
covergroup cg_enc83 (ref logic [7:0] d, ref logic [2:0] y, ref logic valid);
  d_cp : coverpoint d {
    bins onehot[] = {8'h01, 8'h02, 8'h04, 8'h08, 8'h10, 8'h20, 8'h40, 8'h80};
    bins zero     = {8'h00};
  }
  y_cp : coverpoint y {
    bins code[] = {[0:7]};
  }
  valid_cp : coverpoint valid {
    bins invalid = {0};
    bins ok      = {1};
  }
  y_x_valid : cross y_cp, valid_cp;
endgroup
```
